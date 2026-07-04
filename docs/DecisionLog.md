# Atlas Decision Log

This log records architectural decisions that shape future development.

## 2026-07-04: Sprint 257 — Implement --language for Phase 1 Read-Only CLI Commands

Decision: Add `--language {en,sv}` to `atlas weekly-review`, `atlas snapshot validate`, and `atlas snapshot review`. Validate with `ensure_supported_locale`; pass as `locale=language` to the respective renderer. Default remains `"en"`. Deferred commands (`snapshot confirm`, `snapshot reject`, `snapshot export-*`) unchanged.

**Implementation pattern (identical for all three commands):**
1. Add `language: str = typer.Option("en", "--language", help="Output language: en (English, default) or sv (Swedish).")` to the command signature.
2. Import `ensure_supported_locale` and call it immediately inside the command body; catch `ValueError`, print `[red]Unsupported language:[/red] {exc}`, exit code 1.
3. Pass `locale=language` to the renderer call.

**Validation approach:** Post-parse `ensure_supported_locale` (not argparse/Typer `choices`). Rationale: consistent error message format with direct renderer calls; the existing `ValueError` message already names the bad value and supported locales; avoids maintaining a separate CLI-level supported-values list.

**Unsupported-locale behavior:** Fails before any file I/O or rendering. Exit code 1. No partial output. Error message includes the unsupported value and the supported values `'en'` and `'sv'`. Tested for `fr`, `de`, `EN`, `SV`, `en-US`, `sv-SE`, `xx`.

**Backward compatibility:** `--language` omitted → English output identical to pre-Sprint-257. `--language en` → identical to omitted. Verified by `test_weekly_review_language_en_equals_default`, `test_snapshot_validate_language_en_equals_default`, `test_snapshot_review_language_en_equals_default`.

**Sprint 258 recommendation:** Plan Phase 2 CLI language option for write-producing Snapshot commands. After Phase 1 is stable, document the safety boundary for `snapshot confirm`, `snapshot reject`, and `snapshot export-*` before extending `--language` there.

**Result:** 3 command functions updated. 68 new CLI tests. No renderer changes. No locale_support changes. No string module changes. Default English output unchanged. All demos green. RC2 green.

---

## 2026-07-04: Sprint 256 — Plan CLI Language Option Without Implementation

Decision: Create `docs/CLILanguageOptionPlan.md` — the design document for the future `--language {en,sv}` CLI option. No production code changed. `--language` is not implemented. Swedish internal activation is complete (B1–B14 DONE). CLI language exposure is planned for a future sprint.

**Option shape decided:** `--language {en,sv}`. Rationale: explicit user choice, no automatic detection, direct mapping to `locale_support._SUPPORTED_LOCALES`, avoids environment-variable or config-file language inference.

**Propagation path decided:** CLI parameter → `ensure_supported_locale(language)` validation → renderer `locale=language` argument → `_strings_for_locale(language)` → English or Swedish constants. The CLI must not maintain its own supported-language list independently of `locale_support.py`.

**Rollout order decided:** Phase 1 (read-only commands: `weekly-review`, `snapshot validate`, `snapshot review`) before Phase 2 (write-producing local commands: `snapshot confirm`, `snapshot reject`, `snapshot export-*`). Rationale: read-only commands produce terminal output only — no local files are written — making them the lowest-risk starting point.

**Unsupported locale policy:** Fail before rendering. No fallback to English. No silent coercion. No case normalization. No region-code expansion. Exit non-zero. Name the bad value and the supported values.

**Open questions documented:** argparse `choices` vs post-parse `ensure_supported_locale` validation; per-command vs global `--language` position; Phase 2 timing; Swedish `--help` text (deferred: CLI help is English-only in initial implementation).

**Sprint 257 recommendation:** Implement `--language` for Phase 1 read-only commands.

**Result:** Plan document created. Test file created (67 tests). No runtime behavior changed. CLI output unchanged.

---

## 2026-07-04: Sprint 255 — Create Dedicated sv Activation Full-Suite Gate

Decision: Create `tests/test_sv_activation_full_suite_gate_sprint255.py` — a compact release gate that verifies all 14 Swedish readiness criteria hold together. The file is not a duplicate of prior sprint tests; it checks that the activation artifacts exist and that essential safety invariants still hold as a combined gate. Marks B14 DONE. 14 of 14 blocking criteria satisfied.

**Rationale:** After B1–B13 are individually satisfied by eight dedicated test files, a combined gate is needed to ensure no criterion has regressed and that the activation state is coherent as a whole. A single gate file is the right shape — compact, dependency-declaring (prior test files must exist), and unambiguous about the final activation status.

**Swedish activation state at Sprint 255:**
- Swedish is active in direct renderer calls (`render_weekly_review(..., locale="sv")`, all Snapshot renderer functions with `locale="sv"`)
- Swedish is internal only — CLI output remains English
- No `--language` CLI option exists
- Supported locales: `"en"` and `"sv"` only
- Any future CLI language option requires a separate planning sprint

**Readiness checklist:** B14 marked DONE. All 14 of 14 blocking criteria satisfied. Swedish internal activation is complete.

**Sprint 256 recommendation:** Plan CLI language option without implementation. Now that all Swedish internal activation criteria are complete, the next step should be planning the user-facing `--language` option and its safety boundaries — documenting the design, migration path, locale forwarding, and error handling — before any implementation begins.

**Result:** Gate test file added. No runtime behavior changed. No production code changes. CLI output unchanged.

---

## 2026-07-04: Sprint 254 — Add Unsupported-Locale Regression Matrix

Decision: Create `tests/test_unsupported_locale_regression_sprint254.py` — a systematic regression matrix covering the full locale-aware renderer surface after `sv` activation. Tests that 13 unsupported locale values (`fr`, `de`, `ja`, `no`, `da`, `fi`, `es`, `xx`, `""`, `EN`, `SV`, `en-US`, `sv-SE`) raise `ValueError` from `ensure_supported_locale`, `render_weekly_review`, and all 14 public Snapshot locale-aware renderer functions. Supported locales verified to remain exactly `"en"` and `"sv"`. Error message quality verified: unsupported locale named, supported locales listed.

**Rationale:** After `sv` activation (B5), any new supported locale must be explicitly added to the allowlist in `locale_support.py`. This test matrix ensures the allowlist boundary is enforced consistently across the full renderer surface — not just the spot-checks scattered in prior sprint tests. Without a dedicated regression matrix, a future dispatch change could silently broaden the boundary.

**Key properties verified:**
- `_SUPPORTED_LOCALES` is exactly `frozenset({"en", "sv"})` — no extras
- No other language code appears in `locale_support.py` as a supported value
- Uppercase variants (`EN`, `SV`) fail — locale matching is exact, not case-folded
- Region variants (`en-US`, `sv-SE`) fail — no partial matching
- Empty string fails — no default fallback
- `en` and `sv` still pass in all renderer functions after the full regression run

**Readiness checklist:** B13 marked DONE. B14 remains OPEN. 13 of 14 criteria satisfied.

**Sprint 255 recommendation:** Dedicated sv activation full-suite gate (B14). Now that B13 is complete, only B14 remains. Atlas needs a dedicated test gate that proves the complete sv-internal activation (all B1–B13 tests combined) remains green, CLI stays English, demos pass, and the RC check is clean — before any CLI exposure or user-facing language option is considered.

**Result:** Tests added. No runtime behavior changed. No locale_support.py changes. No renderer changes. CLI output unchanged.

---

## 2026-07-04: Sprint 253 — Add Swedish Canonical Value and User-Content Passthrough Matrix

Decision: Create `tests/test_swedish_canonical_passthrough_sprint253.py` — a systematic matrix verifying that Swedish-locale output does not translate canonical internal values or user-provided content. Covers all 8 SnapshotType values, all 5 SnapshotConfirmationStatus values, all 4 SnapshotConfidence values, warning codes, warning code format, en/sv warning code parity, ticker symbols, file paths, scope notes, watchlist reasons, research note text, journal entries, snapshot notes, source descriptions, extracted field values, render idempotency, and English output preservation.

**Rationale:** After B6–B10 prove that Atlas-generated display strings are Swedish and safe, the next safety gate is systematic evidence that the Swedish renderer does not touch values it must never translate: canonical enum strings, user-written content, and internal path identifiers. Without this gate, a future string dispatch change could accidentally translate a warning code or ticker symbol and produce silent data corruption.

**Key invariants verified:**
- `render_weekly_review(result, locale="sv")` does not mutate `result` fields
- `render_weekly_review(result, locale="sv")` is idempotent
- English output is identical before and after calling the Swedish renderer
- Warning codes are identical between `sv` and `en` output
- All user-provided content (scope notes, watchlist reasons, research notes, journal entries, snapshot fields) passes through unchanged in Swedish output

**Readiness checklist:** B11 and B12 marked DONE. B13 and B14 remain OPEN. 12 of 14 criteria satisfied.

**Sprint 254 recommendation:** Add unsupported-locale regression matrix (B13). Now that canonical values and user content are verified safe, the remaining safety gate before any CLI exposure is a systematic regression test confirming that all unsupported locales (`fr`, `de`, `ja`, etc.) still raise `ValueError` from both renderers and `ensure_supported_locale`. This ensures the allowlist boundary is enforced across all 14+ Snapshot renderer functions and the Weekly Review renderer.

**Result:** Tests added. No runtime behavior changed. No locale_support.py changes. No renderer changes. No string module changes. CLI output unchanged.

---

## 2026-07-04: Sprint 252 — Create Swedish Output Test Matrix

Decision: Create `tests/test_swedish_output_matrix_sprint252.py` — a systematic Swedish output test matrix covering all Atlas-generated Swedish strings from direct renderer calls. Render full Swedish output and assert all 10 Weekly Review section titles, all body labels, the disclaimer, input status templates, warnings, all 6 Snapshot headings, all safety boundary labels, forbidden-category scan for all 7 prohibited categories, canonical value preservation, user content passthrough, English output unchanged, and CLI English preservation.

**Renderer bug fixed:** Two hardcoded English phrases in Weekly Review section 10 bypassed `S` for locale dispatch:
- `"Reminder: No action is a valid and often appropriate outcome of a weekly review."` — now `S.REMINDER_NO_ACTION_VALID`
- `"Atlas supports better judgment. It does not replace it."` — now `S.REMINDER_ATLAS_SUPPORTS_JUDGMENT`
Added `REMINDER_NO_ACTION_VALID` and `REMINDER_ATLAS_SUPPORTS_JUDGMENT` to both `atlas/weekly_review/strings.py` and `atlas/weekly_review/strings_sv.py`. English content is identical to the previous hardcoded strings. Swedish content approved against `docs/SwedishSafeLanguageGuardrails.md`.

**Rationale:** B6–B10 require tests on actual rendered Swedish output, not just the string constants modules. The test matrix proves all approved Swedish strings appear in renderer output, the forbidden-category scan passes, and that English remains the default. This is the prerequisite for B11–B12 (canonical value and passthrough preservation matrices).

**Readiness checklist:** B6, B7, B8, B9, B10 marked DONE. B11–B14 remain OPEN. 10 of 14 criteria satisfied.

**Sprint 253 recommendation:** Add canonical value and user-content passthrough matrix for Swedish output (B11 and B12). After the main output matrix proves all display strings are Swedish and safe, the next safety gate is a systematic test that Swedish output does not translate canonical internal values or user-provided content across the full range of fixture types.

**Result:** 91 new tests. 3443 total passed. No runtime behavior changed. CLI output unchanged. `sv` is supported only in direct renderer calls.

---

## 2026-07-04: Sprint 251 — Enable sv Locale Internally Without CLI Exposure

Decision: Update `atlas/locale_support.py` to add `SUPPORTED_LOCALE_SV = "sv"` and accept `"sv"` in `ensure_supported_locale`. The `sv` renderer dispatch branch in both `atlas/weekly_review/render.py` and `atlas/snapshot_input/render.py` is now reachable. `render_weekly_review(result, locale="sv")` produces Swedish display strings. All 14 Snapshot renderer functions produce Swedish display strings when called directly with `locale="sv"`. CLI output remains English. No `--language` option. Default locale unchanged.

**Rationale:** B3 (string constants) and B4 (renderer dispatch boundary) were complete. B5 is the minimum change to make Swedish output reachable in code without touching the CLI. The activation is internal-only: no user-visible CLI change is made, no default is changed, no schema or enum is touched. B6–B14 (output test matrix, forbidden-category scan, canonical value preservation, passthrough, regression) remain as the safety gate before any CLI exposure is considered.

**`atlas/locale_support.py` changes:**
- `SUPPORTED_LOCALE_SV = "sv"` constant added
- `_SUPPORTED_LOCALES = frozenset({"en", "sv"})` internal set
- `ensure_supported_locale` now checks `locale not in _SUPPORTED_LOCALES` instead of `locale != SUPPORTED_LOCALE_EN`
- Error message updated: `"Supported locales: 'en', 'sv'."` instead of `"Only 'en' is currently supported."`

**Safety:** Default CLI and renderer output is byte-for-byte identical. `ensure_supported_locale("fr")` still raises. All tests from sprints 244–250 updated to use `"fr"` as the unsupported-locale test value where they previously used `"sv"`. No gettext. No string catalogs. No locale detection. No network calls. No schemas changed.

**Readiness checklist:** B5 marked DONE. B6–B14 remain OPEN. 5 of 14 criteria satisfied.

**Sprint 252 recommendation:** Create Swedish output test matrix (B6–B10 combined). Now that sv is reachable, Atlas needs a focused test file that renders full Swedish output and asserts all section titles, all labels, the disclaimer, and all Snapshot CLI headings — the prerequisite for any CLI exposure.

**Result:** 47 new tests. 3352 total passed. Updated sprint 244–250 tests to reflect sv activation. No runtime behavior changed for CLI users.

---

## 2026-07-04: Sprint 250 — Define Swedish Renderer Dispatch Without Enabling sv

Decision: Add `_strings_for_locale(locale)` dispatch helpers to both `atlas/weekly_review/render.py` and `atlas/snapshot_input/render.py`. The dispatch helper calls `ensure_supported_locale(locale)` first, maps `"en"` to English string constants, and maps `"sv"` to Swedish string constants. The `sv` branch is structurally present but physically unreachable at runtime because `locale_support.py` still raises for `"sv"`. `atlas/locale_support.py` is unchanged. `sv` remains unsupported.

**Rationale:** B4 (renderer dispatch boundary) is a prerequisite for B5 (locale_support.py update). Wiring the dispatch before enabling the locale means that when B5 is completed, the render path is fully ready. The safety layer (`ensure_supported_locale`) is called unconditionally inside the dispatch helper, so the architectural separation between locale-support activation (B5) and renderer readiness (B4) is enforced by code, not just convention.

**`atlas/weekly_review/render.py` changes:**
- Renamed import: `from atlas.weekly_review import strings as strings_en`
- Added import: `from atlas.weekly_review import strings_sv as strings_sv`
- Added `_strings_for_locale(locale)` dispatch helper
- `render_weekly_review` now calls `S = _strings_for_locale(locale)` instead of bare `ensure_supported_locale(locale)`
- Removed module-level `_TITLE` constant; `S.WEEKLY_REVIEW_TITLE` used inline
- All section helpers and `_render_journal_aging_note` now take `S` as a parameter

**`atlas/snapshot_input/render.py` changes:**
- Renamed import: `from atlas.snapshot_input import strings as strings_en`
- Added import: `from atlas.snapshot_input import strings_sv as strings_sv`
- Added `_strings_for_locale(locale)` dispatch helper
- All 14 public render functions now call `S = _strings_for_locale(locale)` instead of `_ensure_locale(locale)`

**Safety:** Default English output is byte-for-byte identical to pre-Sprint 250. `render_weekly_review(result, locale="sv")` and all 14 Snapshot render functions still raise `ValueError` for `locale="sv"`. No new CLI options. No gettext. No network calls.

**Readiness checklist:** B4 marked DONE. B5–B14 remain OPEN. 4 of 14 criteria satisfied.

**Sprint 251 recommendation:** Update `atlas/locale_support.py` to accept `"sv"` (B5). Prerequisite: B3 and B4 now DONE. B5 is the gate between dispatch-ready and runtime-active.

**Result:** 37 new tests. 3303 total passed. No runtime behavior changed. `sv` is not enabled.

---

## 2026-07-04: Sprint 249 — Define Swedish Display String Constants

Decision: Create `atlas/weekly_review/strings_sv.py` and `atlas/snapshot_input/strings_sv.py` — isolated Swedish display string constants modules. Neither module is imported by any active renderer. `atlas/locale_support.py` is unchanged. `sv` remains unsupported.

**Rationale:** Sprint 248 defined 14 blocking criteria before `sv` can be enabled. B3 (Swedish string constants) is the prerequisite for B4 (renderer dispatch). Creating the constants first — with no renderer wiring — keeps each increment safe and independently verifiable.

**`atlas/weekly_review/strings_sv.py` contents:**
- `WEEKLY_REVIEW_TITLE` — "Atlas veckovis investeringsgranskning"
- All 10 section titles (`SECTION_REVIEW_SCOPE` → "1. Granskningens omfattning", etc.)
- `WEEKLY_REVIEW_SECTION_TITLES` 10-tuple
- All 7 repeated body labels (`LABEL_EVIDENCE_GAP` → `Underlagslucka`, `LABEL_RISK_TO_MONITOR` → `Risk att följa`, etc.)
- `LABEL_INPUT_STATUS` → `Indatastatus`, `LABEL_INPUT_WARNINGS` → `Indatavarningar`
- All 14 `INPUT_STATUS_*` message templates with `{count}`, `{name}`, `{date}` placeholders
- `WARNING_ROW` and `WARNING_SCOPE_SUMMARY` templates
- `WEEKLY_REVIEW_DISCLAIMER` two-line form (deterministisk / stöder bättre omdöme)

**`atlas/snapshot_input/strings_sv.py` contents:**
- All 6 command headings (`HEADING_VALIDATION` → "Validering av Snapshot Draft", etc.)
- All 7 status display lines
- Exportability lines (`EXPORTABLE_YES` → "Exporterbar: ja", etc.)
- All 9 section header labels (including `SECTION_SAFETY_BOUNDARY` → "Säkerhetsgräns:")
- All safety boundary lines (validate, review, confirm, reject, research notes, company facts)
- All 3 confirm/reject note lines

**Safety:** All Swedish wording follows `docs/SwedishSafeLanguageGuardrails.md`. No recommendation, urgency, price-target, certainty, execution, outperformance, or personalized advice language. No canonical enum values, schema keys, or warning codes translated.

**Readiness checklist:** B3 marked DONE. B4–B14 remain OPEN. 3 of 14 criteria satisfied.

**Sprint 250 recommendation:** Define Swedish renderer dispatch without enabling `sv`.

**Result:** 94 new tests. 3266 total passed. No runtime behavior changed. `sv` is not enabled.

---

## 2026-07-04: Sprint 248 — Swedish Localization Readiness Checklist

Decision: Create `docs/SwedishLocalizationReadinessChecklist.md` — a documentation-only sprint that defines the exact go/no-go criteria before `"sv"` may be added to `atlas/locale_support.py`. No Swedish renderer implemented. No locale changes.

**Rationale:** Sprint 247 defined what Swedish output must not say (guardrails). Sprint 248 defines what must exist and pass before Swedish output is enabled (readiness). This checklist is the operational complement to the guardrail spec: a structured gate that prevents premature activation.

**Document contents:**
- Purpose and scope
- Non-Goals
- 14 blocking criteria (B1–B14), each with explicit sub-items:
  - B1: Guardrail specification (DONE, Sprint 247)
  - B2: This readiness checklist (DONE, Sprint 248)
  - B3: Swedish string constants modules
  - B4: Swedish renderer integration
  - B5: `locale_support.py` updated to accept `"sv"`
  - B6: Forbidden-category scan tests
  - B7: Swedish heading output tests
  - B8: Swedish label output tests
  - B9: Swedish disclaimer output test
  - B10: Swedish Snapshot CLI heading tests
  - B11: Canonical value preservation tests
  - B12: User-provided content passthrough tests
  - B13: Unsupported locale regression tests
  - B14: Full suite green with sv enabled
- 5 non-blocking criteria (N1–N5) for post-activation polish
- Current status table (2 of 14 DONE)
- How to activate `sv` (step-by-step with ordering warning)
- Recommended implementation order across future sprints

**Sprint 249 recommendation:** Create `atlas/weekly_review/strings_sv.py` with all approved Swedish section titles and labels (B3, first half).

**Result:** 64 new tests. 3172 total passed. No runtime behavior changed. `sv` is not enabled.

---

## 2026-07-04: Sprint 247 — Swedish Safe-Language Guardrail Specification

Decision: Create `docs/SwedishSafeLanguageGuardrails.md` — a documentation-only sprint that defines the safety layer required before Atlas may generate Swedish output. No Swedish renderer is implemented. No `sv` locale is enabled. `atlas/locale_support.py` is unchanged.

**Rationale:** Sprint 246 centralized the locale boundary. Before any non-English locale can be enabled, that locale must have its own safe-language guardrail list — a prerequisite established in `docs/AtlasLocalizationBoundary.md`. This sprint satisfies that prerequisite for Swedish. It does not satisfy it for French (Sprint 248 recommendation).

**Document contents:**
- Purpose and scope
- Non-Goals (no translations, no `sv`, no gettext, no `--language`)
- Core Swedish Output Principle (Swedish and English)
- 7 prohibited language categories (recommendation, transaction, price-target, urgency, certainty, outperformance, personalized advice) with guardrail-context-only examples
- Safe Swedish alternatives table (~25 entries including `Kräver mer underlag`, `Bevakningslista`, `Beslut uppskjutet`, `Ingen åtgärd motiverad`, `Skäl att avvakta`, `Underlagslucka`, `Risk att följa`, `Säkerhetsgräns`)
- Atlas concept mapping (Weekly Review title, 10 section titles, disclaimer, Snapshot CLI headings)
- Swedish Weekly Review style rules (10 rules)
- Swedish Snapshot CLI style rules (6 rules)
- User-provided Swedish content handling
- Guardrail-sensitive phrase table
- 10 testing requirements that must pass before `sv` can be enabled
- Remaining gaps and Sprint 248 recommendation

**Sprint 248 recommendation:** Create French safe-language guardrail specification.

**Result:** 55 new tests. 3108 total passed. No runtime behavior changed. `sv` is not enabled.

---

## 2026-07-04: Sprint 246 — Create Shared Locale Boundary Helper

Decision: Create `atlas/locale_support.py` with `SUPPORTED_LOCALE_EN = "en"` and `ensure_supported_locale(locale: str) -> None`. Update `atlas/weekly_review/render.py` and `atlas/snapshot_input/render.py` to import and use the shared helper. Remove duplicate local `_SUPPORTED_LOCALE` and `_ensure_locale` definitions from both modules.

**Rationale:** Sprints 244 and 245 added equivalent locale guards independently to both renderers. Sprint 246 eliminates that duplication. The shared module is the single canonical source for Atlas locale validation — future locale work (adding `"sv"`, etc.) requires changing only `atlas/locale_support.py`. Both renderers now express `ensure_supported_locale(locale)` at their locale boundary, with no inline guard logic.

**Files changed:**
- `atlas/locale_support.py` — created (16 lines: module docstring, `SUPPORTED_LOCALE_EN`, `ensure_supported_locale`)
- `atlas/weekly_review/render.py` — inline `if locale != "en": raise ...` replaced with `ensure_supported_locale(locale)`; import added
- `atlas/snapshot_input/render.py` — local `_SUPPORTED_LOCALE` and `def _ensure_locale` removed; `ensure_supported_locale` imported as `_ensure_locale` (preserving all existing call sites)

**Error message preserved:** `"Unsupported locale: {locale!r}. Only 'en' is currently supported."` — unchanged.

**Sprint 247 recommendation:** Create Swedish guardrail list — define which Atlas safe-language terms map to Swedish equivalents, establishing the safety layer before any Swedish output is allowed.

**Result:** 31 new tests. 3053 total passed. All demos green. RC2 green. No runtime behavior changed.

---

## 2026-07-04: Sprint 245 — Define Locale-Aware Snapshot CLI Rendering Helper

Decision: Add `*, locale: str = "en"` keyword-only parameter to all 14 public Snapshot CLI renderer functions in `atlas/snapshot_input/render.py`. A shared `_ensure_locale(locale)` helper and `_SUPPORTED_LOCALE = "en"` constant guard each function. Unsupported locales raise `ValueError` immediately. Default behavior and all output are unchanged. The CLI does not expose `--language`.

**Rationale:** Sprint 244 established the locale boundary for Weekly Review. Sprint 245 applies the same boundary to Snapshot CLI, completing the explicit locale handoff surface for both rendering layers. With both renderers having `locale="en"` boundaries, a future Sprint 246 can centralize the repeated validation into a single shared helper across modules.

**Implementation:** `_SUPPORTED_LOCALE = "en"` and `_ensure_locale(locale: str) -> None` added near the top of `atlas/snapshot_input/render.py`. All 14 public functions patched — 11 single-argument-style functions and 3 multi-argument functions (`render_snapshot_confirm_success`, `render_snapshot_reject_success`, `render_snapshot_draft_validation`, `render_snapshot_draft_review`) — each with `_ensure_locale(locale)` as their first statement.

**Locale rules (Sprint 245):**
- Supported locale: `"en"`
- Default: keyword-only `locale: str = "en"`
- Unsupported: `ValueError` naming the bad locale and citing `"en"`
- CLI: unchanged — no `--language`, no `locale=` call sites

**Note:** Sprint 244 test `test_snapshot_render_no_locale_param` was updated — it checked that `locale=` was absent from snapshot render module, which is no longer correct after Sprint 245. Replaced with `test_snapshot_render_no_weekly_review_imports` which tests the correct boundary (snapshot render does not import weekly review).

**Sprint 246 recommendation:** Create shared locale boundary helper — centralize `_ensure_locale` and `_SUPPORTED_LOCALE` into a single `atlas/locale.py` or `atlas/rendering.py` module referenced by both renderers, eliminating duplication without changing behavior.

**Result:** 38 new tests. 3022 total passed. All demos green. RC2 green. No runtime behavior changed.

---

## 2026-07-04: Sprint 244 — Define Locale-Aware Weekly Review Rendering Helper

Decision: Add `*, locale: str = "en"` as a keyword-only parameter to `render_weekly_review` in `atlas/weekly_review/render.py`. Unsupported locales raise `ValueError` immediately. Default behavior and all output are unchanged. The CLI does not expose `--language`. No translations are implemented.

**Rationale:** Sprints 238–243 centralized all bounded Atlas-generated display strings from the Weekly Review and Snapshot CLI renderers into constants modules. Sprint 244 establishes the explicit rendering boundary that future locale work will target. Without this boundary, future translation attempts would require discovering the locale handoff point under time pressure. Adding it now — as a keyword-only parameter with an explicit guard and no implementation — is the minimum viable boundary: one function call site, zero behavior change, zero translation work.

**Design choice:** Option B (extend existing `render_weekly_review` signature) selected over Option A (rename to `_render_weekly_review_en` + new public wrapper) because the CLI and test suite import `render_weekly_review` by name; renaming the internal function would require wider changes with no localization benefit yet.

**Locale rules (Sprint 244):**
- Supported locale: `"en"`
- Default locale: `"en"` (keyword-only, `locale: str = "en"`)
- Unsupported locale: `ValueError` with message naming the bad locale and `"en"` as the supported option
- CLI: unchanged — no `--language`, always uses default
- No translations, no gettext, no locale detection, no locale files

**Sprint 245 recommendation:** Define locale-aware Snapshot CLI rendering helper — same minimal `locale="en"` boundary applied to `atlas/snapshot_input/render.py`.

**Result:** 30 new tests. 2984 total passed. All demos green. RC2 green. No runtime behavior changed.

---

## 2026-07-04: Sprint 243 — Extract Weekly Review Warning Display Templates Into Constants

Decision: Extract the two Atlas-generated warning display format strings from `atlas/weekly_review/render.py` into named constants in `atlas/weekly_review/strings.py`. Warning codes remain canonical internal values and are not extracted. Warning messages in `inputs.py` remain inline because they embed dynamic file paths that cannot be cleanly templated without structural changes.

**Rationale:** After input status messages were centralized in Sprint 242, the remaining bounded Atlas-generated display strings in the warning rendering path were the row format and the scope section summary. These are structural display templates — not user content, not canonical codes — and belong alongside the other display string constants. Warning codes (`missing_optional_profile`, etc.) are internal identifiers and intentionally remain in `inputs.py`.

**Constants added to `atlas/weekly_review/strings.py`:**
- `WARNING_ROW = "- [{code}] {message}"` — row format for each warning in `## Input Warnings`
- `WARNING_SCOPE_SUMMARY = "Warnings: {count} input warning(s) noted — see Input Warnings section"` — scope section summary line

**What stayed out:** warning codes (canonical internal values), warning messages in `inputs.py` (dynamic paths embedded), all body-section generated prose.

**Output preservation:** warning rows verified byte-for-byte unchanged — `- [missing_optional_profile] No investor profile path provided...` format confirmed. Scope summary line confirmed. Full-input output (no-warning path) verified.

**Warning codes:** remain in `inputs.py` as string literals. Not extracted to display constants. Tests verify codes do not appear as named constants in `strings.py`.

**Sprint 244 recommendation:** Define locale-aware rendering helper — a minimal `render_weekly_review(result, locale="en")` signature stub that passes through to the current renderer, establishing the locale parameter boundary without implementing translation.

**Result:** 30 new tests. 2954 total passed. All demos green. RC2 green. No runtime behavior changed.

---

## 2026-07-04: Sprint 242 — Extract Weekly Review Input Status Messages Into Constants

Decision: Extract all 14 `_render_input_status` message templates from inline f-string literals in `atlas/weekly_review/render.py` into named constants in `atlas/weekly_review/strings.py`. Dynamic values (counts, names, dates) remain as `.format(...)` slots. No output changed.

**Rationale:** After section titles, repeated labels, and the disclaimer were centralized, `_render_input_status` remained the highest-concentration source of inline display strings in the renderer. Its messages are bounded, patterned, and appear in every Weekly Review output. Centralizing them completes the extraction of all structured status display text from the renderer, leaving only body-section prose and warning explanations inline.

**Constants added to `atlas/weekly_review/strings.py`:**
- `INPUT_STATUS_PORTFOLIO_LOADED` — `"Portfolio: {count} holding(s) loaded."`
- `INPUT_STATUS_WATCHLIST_LOADED` — `"Watchlist: {count} item(s) loaded from '{name}'."`
- `INPUT_STATUS_INVESTOR_PROFILE_AVAILABLE` — `"Investor profile: Available"`
- `INPUT_STATUS_INVESTOR_PROFILE_NOT_PROVIDED` — `"Investor profile: Not provided — default will be used."`
- `INPUT_STATUS_JOURNAL_LOADED` — `"Decision journal: {count} entry/entries loaded."`
- `INPUT_STATUS_JOURNAL_NOT_PROVIDED` — `"Decision journal: Not provided."`
- `INPUT_STATUS_COMPANY_FACTS_AVAILABLE` — `"Company facts: Available"`
- `INPUT_STATUS_COMPANY_FACTS_NOT_PROVIDED` — `"Company facts: Not provided — evidence gaps noted."`
- `INPUT_STATUS_FINANCIALS_AVAILABLE` — `"Financials: Available"`
- `INPUT_STATUS_FINANCIALS_NOT_PROVIDED` — `"Financials: Not provided — evidence gaps noted."`
- `INPUT_STATUS_RESEARCH_NOTES_LOADED` — `"Research notes: {count} ticker(s) with local notes."`
- `INPUT_STATUS_RESEARCH_NOTES_NOT_PROVIDED` — `"Research notes: Not provided."`
- `INPUT_STATUS_REVIEW_DATE` — `"Review date: {date}"`
- `INPUT_STATUS_WARNINGS_COUNT` — `"Warnings: {count}"`

**What stayed out:** warning body prose (`_render_warnings` message content), all body-section generated text, `_render_journal_aging_note` text, section body labels already extracted in Sprint 240.

**Output preservation:** full-input and minimal-input Weekly Review output verified line-for-line identical. Both loaded and not-provided paths confirmed.

**Sprint 243 recommendation:** Extract Weekly Review warning explanations into constants.

**Result:** 52 new tests. 2924 total passed. All demos green. RC2 green. No runtime behavior changed.

---

## 2026-07-04: Sprint 241 — Extract Weekly Review Disclaimer Into Constant

Decision: Move the two-line Weekly Review disclaimer from a module-level `_DISCLAIMER` variable in `atlas/weekly_review/render.py` into `atlas/weekly_review/strings.py` as `WEEKLY_REVIEW_DISCLAIMER`. Renderer updated to reference `S.WEEKLY_REVIEW_DISCLAIMER`. No wording, punctuation, or spacing changed.

**Rationale:** The disclaimer is the most visible guardrail-sensitive string in the Weekly Review output — it asserts the tool's deterministic, non-recommendation nature. Centralizing it alongside section titles and labels completes the extraction of all structural and guardrail strings from the renderer. Future locale work can now translate or adapt the disclaimer from a single canonical location.

**Constant added to `atlas/weekly_review/strings.py`:**
- `WEEKLY_REVIEW_DISCLAIMER` — two-line disclaimer string, wording preserved exactly.

**What stayed out:** all body prose, input status message templates, warning explanations, and `_section()` helper strings remain inline.

**Sprint 242 recommendation:** Extract Weekly Review input status messages into constants.

**Result:** 25 new tests. 2872 total passed. All demos green. RC2 green. No runtime behavior changed.

---

## 2026-07-04: Sprint 240 — Extract Weekly Review Section Labels Into Constants

Decision: Extend `atlas/weekly_review/strings.py` with 9 repeated section body label constants. Update `atlas/weekly_review/render.py` with ~20 targeted replacements referencing `S.LABEL_*` constants. No output changed.

**Rationale:** Sprint 239 extracted the 10 structural section titles. Sprint 240 extracts the repeated semantic labels that appear in generated body text across multiple sections — `Evidence Gap`, `Risk to Monitor`, `Reason to Wait`, etc. These labels carry meaningful semantics (they form the user-visible taxonomy of the tool's output), and centralizing them prevents drift, makes future locale work tractable, and eliminates the risk of inconsistent capitalization across sections.

**Constants added to `atlas/weekly_review/strings.py`:**
- `LABEL_EVIDENCE_GAP = "Evidence Gap"`
- `LABEL_RISK_TO_MONITOR = "Risk to Monitor"`
- `LABEL_REASON_TO_WAIT = "Reason to Wait"`
- `LABEL_DECISION_DEFERRED = "Decision Deferred"`
- `LABEL_NO_ACTION_WARRANTED = "No Action Warranted"`
- `LABEL_AGING_NOTE = "Aging Note"`
- `LABEL_MISSING_OPTIONAL_INPUT = "Missing Optional Input"`
- `LABEL_INPUT_STATUS = "Input Status"`
- `LABEL_INPUT_WARNINGS = "Input Warnings"`

**Scope constraints honored:** enum values (`confirmed`, `rejected`, `research_notes_snapshot`) remain inline. User-provided passthrough content (research notes, scope notes) remain inline. `_DISCLAIMER` not touched. No output wording, capitalization, punctuation, or blank lines changed.

**Output preservation:** all label strings verified unchanged in representative Weekly Review output. Evidence Gap, Risk to Monitor, Reason to Wait, No Action Warranted, Missing Optional Input, Input Status all confirmed present with correct formatting.

**Sprint 241 recommendation:** Extract CLI help text and top-level command descriptions into constants, or extract `_DISCLAIMER` into a named constant.

**Result:** 38 new tests. 2847 total passed. All demos green. RC2 green. No runtime behavior changed.

---

## 2026-07-04: Sprint 239 — Extract Weekly Review Section Titles Into Constants

Decision: Create `atlas/weekly_review/strings.py` containing the 10 Weekly Review section title constants and the document title. Update `atlas/weekly_review/render.py` to reference these constants via `from atlas.weekly_review import strings as S`. No output changed.

**Rationale:** Sprint 238 established the extraction pattern for Snapshot CLI strings. Sprint 239 applies the same pattern to the most bounded Weekly Review strings — the 10 section titles — before touching body text or locale-aware rendering. Centralizing section titles makes the section structure explicit and refactor-safe, with no behavioral risk.

**Constants extracted to `atlas/weekly_review/strings.py`:**
- `WEEKLY_REVIEW_TITLE = "Atlas Weekly Investment Review"`
- 10 section title constants (`SECTION_REVIEW_SCOPE` through `SECTION_NON_ACTIONS_REASONS_TO_WAIT`)
- `WEEKLY_REVIEW_SECTION_TITLES` — ordered tuple of all 10 titles

**What stayed out of constants:** all body text, `_DISCLAIMER`, section labels (`Evidence Gap`, `Reason to Wait`, input status labels), formatting strings. Only the 10 structural section titles and document title were extracted.

**Output preservation:** all 10 section headings verified identical before and after (`## 1. Review Scope` through `## 10. Non-Actions / Reasons to Wait`). Full representative Weekly Review command confirmed green.

**Sprint 240 recommendation:** Extract Weekly Review section labels into constants (repeated body labels: `Evidence Gap`, `Risk to Monitor`, `Reason to Wait`, input status messages).

**Result:** 38 new tests. 2809 total passed. All demos green. RC2 green. No runtime behavior changed.

---

## 2026-07-04: Sprint 238 — Extract Snapshot CLI Display Strings Into Constants

Decision: Create `atlas/snapshot_input/strings.py` containing all Snapshot CLI display string constants. Update `atlas/snapshot_input/render.py` to import and reference these constants. No output changed.

**Rationale:** Sprint 237 inventoried all user-facing strings. Sprint 238 acts on that inventory for the lowest-risk target — Snapshot CLI strings — which are smaller and more bounded than Weekly Review output. Centralizing display strings creates the extraction pattern needed before any locale-aware rendering layer can be added.

**Constants extracted to `atlas/snapshot_input/strings.py`:**
- 6 command headings (`HEADING_VALIDATION`, `HEADING_REVIEW`, `HEADING_CONFIRMATION`, `HEADING_REJECTION`, `HEADING_RESEARCH_NOTES_EXPORT`, `HEADING_COMPANY_FACTS_EXPORT`)
- 7 status display lines (`STATUS_VALID`, `STATUS_INVALID`, `STATUS_REVIEWABLE`, `STATUS_BLOCKED`, `STATUS_WRITTEN`, `STATUS_CONFIRMED`, `STATUS_REJECTED`)
- Exportability lines (`EXPORTABLE_YES`, `EXPORTABLE_NO`, `EXPORTABLE_NO_REASON`)
- 9 section header labels (`SECTION_SAFETY_BOUNDARY`, `SECTION_SOURCE`, `SECTION_REVIEW_CHECKLIST`, `SECTION_UNCERTAINTIES`, `SECTION_MISSING_REQUIRED_FIELDS`, `SECTION_MISSING_REQUIRED_FIELDS_WARNINGS`, `SECTION_EXTRACTED_FIELDS`, `SECTION_BLOCKING_ISSUES`, `SECTION_RESEARCH_NOTES_REVIEW`)
- 12 safety boundary lines (validation, review, confirm, reject, research notes export, company facts export)
- 3 confirm/reject note lines

**What stayed out of constants:** canonical enum values (`confirmed`, `rejected`, `research_notes_snapshot`, etc.), user-provided content, f-string value slots.

**Output preservation:** all 6 representative CLI commands verified byte-for-byte unchanged before and after extraction.

**Canonical values unchanged:** all `SnapshotConfirmationStatus` and `SnapshotType` enum values confirmed stable.

**Sprint 239 recommendation:** Extract Weekly Review section titles into constants (10 bounded strings, structural, low risk).

**Result:** 64 new tests. 2771 total passed. All demos green. RC2 green. No runtime behavior changed.

---

## 2026-07-04: Sprint 237 — Extract User-Facing Strings Inventory

Decision: Create `docs/AtlasUserFacingStringsInventory.md` as Phase 1 of the localization plan — a complete audit of all Atlas-generated display strings without changing any runtime behavior.

**Rationale:** The localization boundary (Sprint 236) defined which strings may eventually be translated. The inventory makes that abstract boundary concrete and testable. It enumerates every Atlas-generated display string across the Weekly Review renderer and Snapshot CLI renderer, classifies each as `localizable_display`, `canonical_internal`, `user_content_passthrough`, `command_or_file_convention`, or `guardrail_sensitive_display`, and identifies future extraction priority order.

**Key findings:**
- Weekly Review renderer: ~90 distinct string groups across 10 sections + Input Status
- Snapshot CLI renderer: ~50 distinct string groups across 6 commands
- Section 10 (Non-Actions/Reasons to Wait) has the highest density of guardrail-sensitive strings
- Safety Boundary text blocks are the highest-risk localization targets — semantics must be preserved exactly per locale
- All display strings are currently inline literals; no string catalog exists yet

**Canonical internal values inventoried:** All confirmation_status, snapshot_type, confidence enum values; all CLI option and command names; all schema field names; all file/directory conventions.

**User-provided passthrough inventoried:** 17 distinct passthrough contexts — research notes, scope notes, journal entries, profile fields, snapshot draft content. None are localization targets.

**Sprint 238 recommendation:** Extract Snapshot CLI display strings into named constants (lowest-risk extraction, bounded scope).

**Result:** 49 new tests. 2707 total passed. No runtime behavior changed.

---

## 2026-07-04: Sprint 236 — Define Localization Boundary

Decision: Create `docs/AtlasLocalizationBoundary.md` to define the boundary between canonical internal English and future user-facing localizable output before any multilingual implementation begins.

**Rationale:** Atlas now has a stable internal v1 demo package. Before the product surface expands further, the architecture must define which strings are permanent canonical English identifiers (enums, schema keys, CLI option names, file conventions) and which are localizable display text (rendered section titles, CLI output messages, explanatory text). This prevents future localization from destabilizing internal logic or test assertions.

**Core principle documented:** Atlas thinks internally in canonical English and may eventually speak externally in the user's selected language.

**Key boundary rules:**
1. Enum values, schema keys, CLI option names, and file conventions remain English permanently
2. Localized display text is generated only at the final rendering layer
3. Tests for logic assert canonical values — they never need to change for localization
4. User-provided content (research notes, scope notes) is not translated
5. Each locale requires its own safe-language guardrail list before activation
6. Missing localization fails safely to English
7. Localization never changes program behavior — display text only

**Future phases defined (not implemented):** strings inventory → locale-aware renderers → `--language` option → per-locale guardrail tests → Swedish output → French output.

**Result:** 28 new tests. 2658 total passed. All demos green. No runtime behavior changed.

**Sprint 237 recommendation:** Extract user-facing strings inventory.

---

## 2026-07-04: Sprint 235 — Create Internal v1 Demo Package

Decision: Create `docs/InternalV1DemoPackage.md` and `scripts/run_internal_v1_demo.sh` to show the complete safe Atlas user journey in a reproducible, local-only form.

**Rationale:** After six validated portfolio trials, Atlas has a stable enough foundation to package into a documented internal demo. The demo provides a repeatable checkpoint for internal testers and developers before further product surface expansion.

**Deliverables:**
- `docs/InternalV1DemoPackage.md` — full demo guide covering 7 stages: validate, review, confirm, reject, export-research-notes, export-company-facts, weekly-review
- `scripts/run_internal_v1_demo.sh` — executable bash script running all 7 stages end-to-end, writing only to `/tmp/atlas_internal_v1_demo/`, verifying output checkpoints including that rejected drafts are blocked from export
- `tests/test_internal_v1_demo_package_sprint235.py` — 23 tests covering doc and script completeness, safety boundary terms, forbidden language, and command coverage

**Result:** Green. Script runs end-to-end. All 2630 tests pass. RC2 green.

**Sprint 236 recommendation:** Define Localization Boundary — establish what is internal canonical English logic versus future user-facing language output before expanding the product surface further.

---

## 2026-07-04: Sprint 234 — Company Facts Export Trial

Decision: Run sixth portfolio trial validating the full company facts export path: confirmed draft → `export-company-facts` → local `ASML.json` → `weekly-review --company-facts DIR`.

**Rationale:** After adding company facts draft export, Atlas validates the full path from confirmed company facts draft to local company facts file to Weekly Review evidence presence before adding another conversion type.

**Trial result:** Green. All stages clean. ASML section 8 evidence gap cleared when facts file present. Section 9 and 10 improve from generic "no facts" to per-ticker precision. MD5 confirmed draft unchanged throughout. No mutation outside expected output path.

**Key findings:**
1. Section 8 clears the correct ticker only — detection is per-ticker and precise
2. Section 9 adds "Tickers without local company facts (N): …" list when facts are partially present — meaningful precision improvement over no-facts state
3. Section 10 narrows reason-to-wait from "company facts not loaded" to "missing for N ticker(s) (X, Y, Z)" — same precision improvement
4. "Blocking Issues" label in `snapshot review` is slightly confusing when draft is already confirmed and exportable — the correct information is present but a future wording improvement could help
5. overwrite guard and file mutation boundaries confirmed correct

**Sprint 235 recommendation:** Create internal v1 demo package. All conversion paths validated; stable enough for a repeatable internal demo flow before adding higher-risk conversion types.

---

## 2026-07-04: Sprint 233 — Add Snapshot Company Facts Export CLI

Decision: Add `atlas snapshot export-company-facts <draft_path> --output-dir DIR` to convert confirmed `company_facts_snapshot` drafts to `<TICKER>.json`.

**Rationale:** After validating confirm/reject workflow, the next conversion type is company facts — a standalone local file with no cross-dependency on research notes or portfolio. Cleanest first conversion type to validate the end-to-end export pattern for structured fact data.

**Behavior:**
- Only `company_facts_snapshot` type accepted; all others blocked
- Only `confirmed` status accepted; draft/needs_user_review/rejected/superseded all blocked
- Ticker resolved from `extracted_fields["ticker"]` or `related_tickers[0]`; unsafe tickers blocked
- Output: `output_dir/<TICKER>.json` (uppercase ticker)
- Bounded output: 800 char strings, 30 list items, 500 chars per item
- No overwrite by default; `--overwrite` to replace
- No mutation of original draft; no portfolio/watchlist/journal/research notes written
- Source provenance (`draft_id`, `source_description`) written into `source` key

**Trial result:** Green. ASML example draft exported cleanly. `ASML.json` detected by `--company-facts` flag in Weekly Review. Safety boundaries accurate in CLI output.

---

## 2026-07-04: Sprint 232 — Snapshot Confirm and Reject Status Workflow Trial

Decision: Run the full confirm and reject branch trial after adding both `atlas snapshot confirm` and `atlas snapshot reject`.

**Rationale:** After adding both confirm and reject commands, Atlas validates both branches of the basic Snapshot Draft status workflow before adding more conversion types or status lifecycle commands.

**Trial result:** Both branches green. MD5 verified original draft unchanged throughout. Confirm branch: confirmed copy validates, reviews as Exportable: yes, exports cleanly, Weekly Review consumes notes in Sections 8/9/10. Reject branch: rejected copy validates, reviews as Exportable: no, export blocked (exit 1) with no export directory created.

**Key findings:**
1. Branch choice is visible from review output — user sees draft state, exportability, and blocking issues before deciding
2. The confirm three-step chain (confirm → validate → export) is clean and consistent
3. The reject two-step chain (reject → validate/review) is clean; export block is reliable and produces no side effects
4. Safety boundaries are distinct per command and accurate
5. `(research notes)` provenance label in Sections 8/9 remains accurate from confirm branch

**Sprint 233 recommendation:** Implement draft-to-company-facts conversion — safest next conversion type, writes `company_facts/<TICKER>.json`, improves Weekly Review evidence presence.

---

## 2026-07-04: Sprint 231 — Add Snapshot Draft Reject CLI

Decision: Add `atlas snapshot reject <draft_path> --output-draft <path>` as a safe, non-mutating rejection command.

**Rationale:** After validating the review-confirm-export workflow, Atlas adds a safe reject command that writes a new rejected draft copy without mutating the original draft or any Atlas local input files. This completes the basic confirm/reject workflow boundary. Rejected drafts are not exportable; the export commands block them explicitly.

**Behavior:**
- `draft`, `needs_user_review`, `confirmed`, and `rejected` states may produce a rejected copy
- `confirmed` input writes a rejected copy with a note that the input was confirmed
- `rejected` input writes a copy with a note that it was already rejected
- `superseded` state is hard-blocked (superseded drafts were replaced by newer drafts)
- Output path must differ from input path (no in-place rejection)
- Default: refuse to overwrite existing output draft; `--overwrite` enables replacement
- `export-research-notes` blocks rejected copies explicitly

**Changes:**
- `atlas/snapshot_input/reject.py`: new module — `SnapshotRejectResult`, `reject_snapshot_draft`
- `atlas/snapshot_input/render.py`: `render_snapshot_reject_success`, `render_snapshot_reject_blocked`, `render_snapshot_reject_error`
- `atlas/snapshot_input/__init__.py`: updated exports
- `atlas/cli/main.py`: `atlas snapshot reject` command added
- `tests/test_snapshot_draft_reject_cli_sprint231.py`: 55 new tests

**Sprint 232 recommendation:** Run fifth real portfolio trial with confirm and reject — validate both branches of the basic status workflow before adding conversion types.

---

## 2026-07-04: Sprint 230 — Fourth Real Portfolio Trial With Confirm Then Export

Decision: Run the full review-confirm-export-Weekly Review loop with realistic inputs after adding `atlas snapshot confirm`.

**Rationale:** After adding Snapshot Draft review and confirm commands, Atlas validates the complete safe workflow from unconfirmed draft review to confirmed copy to research notes export to Weekly Review before adding more status commands or conversion types.

**Trial result:** All five stages passed. MD5 checksum confirmed original draft unchanged. Confirmed copy validated and reviewed as `Exportable: yes`. Export wrote only `ASML/notes.md`. Weekly Review consumed notes in Sections 8, 9, and 10 with correct provenance labels. Both example and realistic bundles green.

**Key findings:**
1. Collision guard on `confirm` (exit 1 with `--overwrite` hint) is safe and useful
2. `Exportable: yes` in review is a clear gate signal
3. `(research notes)` provenance label in Sections 8/9 keeps source attribution traceable
4. Review blocking issue message on confirmed drafts could be clearer (known gap, logged)
5. Example draft is sparse — richer example would better demonstrate full export

**Sprint 231 recommendation:** Add snapshot draft reject CLI — complete the basic status workflow (confirm/reject) before adding conversion types.

---

## 2026-07-04: Sprint 229 — Add Snapshot Draft Confirm CLI

Decision: Add `atlas snapshot confirm <draft_path> --output-draft <path>` as a safe, non-mutating confirmation command.

**Rationale:** After adding read-only Snapshot Draft review (Sprint 228), Atlas adds a safe confirmation command that writes a new confirmed draft copy without mutating the original draft or any Atlas local input files. This completes the review-before-export boundary: a draft must be reviewed, then explicitly confirmed, before export commands are used. Confirmation is a deliberate human decision recorded as a file — not an automatic promotion. The original draft is preserved to allow audit and comparison.

**Behavior:**
- `draft` and `needs_user_review` states confirm if no blocking issues are found
- `confirmed` input writes a confirmed copy with a note that it was already confirmed
- `rejected` and `superseded` states are hard-blocked
- Output path must differ from input path (no in-place confirmation)
- Default: refuse to overwrite existing output draft; `--overwrite` enables replacement
- All Sprint 227/228 blocking rules apply: unsupported type, empty fields, missing ticker, unsafe ticker

**Changes:**
- `atlas/snapshot_input/confirm.py`: new module — `SnapshotConfirmResult`, `confirm_snapshot_draft`
- `atlas/snapshot_input/render.py`: `render_snapshot_confirm_success`, `render_snapshot_confirm_blocked`, `render_snapshot_confirm_error`
- `atlas/snapshot_input/__init__.py`: updated exports
- `atlas/cli/main.py`: `atlas snapshot confirm` command added
- `tests/test_snapshot_draft_confirm_cli_sprint229.py`: 53 new tests

**Sprint 230 recommendation:** Run fourth real portfolio trial with confirm then export — validate the complete safe workflow: review → confirm copy → validate → export research notes → Weekly Review.

---

## 2026-07-04: Sprint 220 — Second Realistic Weekly Review Trial

Decision: Run a second realistic Weekly Review trial after Sprints 218 and 219 to validate usability before adding deeper engines.

**Rationale:** After adding profile context and per-ticker evidence presence checks, Atlas validates the complete local-only Weekly Review output against realistic inputs before adding deeper engines or new product surfaces. This keeps product development grounded in actual usability rather than feature accumulation.

**Trial findings:** Output was specific and safe, but Sections 8, 9, and 10 were verbose when many tickers lacked local files. Four verbosity problems identified and fixed:
1. Section 8 (24 lines → 12 lines): combined "both missing" into one line per ticker
2. Section 9 (24 lines → 2 lines): replaced per-ticker identical questions with two grouped ticker lists
3. Section 10 missing evidence (24 lines → 2 lines): consolidated into summary lines
4. Section 10 principles/constraints (12 boilerplate lines → 2 block headers + listed items): eliminated repetitive boilerplate

**Section 10 total:** reduced from ~40 lines to ~18 lines.

**Changes:**
- `atlas/weekly_review/render.py`: four renderer condensing changes
- `tests/test_weekly_review_second_trial_sprint220.py`: 20 new tests
- `tests/test_weekly_review_evidence_presence_sprint219.py`: 6 tests updated
- `tests/test_weekly_review_trial_sprint213.py`: 2 tests updated
- `docs/WeeklyReviewSecondTrialFindings.md`: full trial record created

**Next sprint recommendation:** Sprint 221 — Group or simplify Section 10 output (add reason-type headers).

---

## 2026-07-03: Sprint 219 — Per-Ticker Local Evidence Presence Checks in Weekly Review

Decision: Add per-ticker local evidence presence checks to Weekly Review Sections 8, 9, and 10.

**Rationale:** After profile principles and constraints were rendered, the next local-only improvement is to make Missing Evidence more specific by checking which portfolio and watchlist tickers have local company facts and financial history files. This improves follow-up quality without adding provider, engine, or live-data dependencies.

**Changes:**
- `atlas/weekly_review/inputs.py`: Added `WeeklyReviewTickerEvidence` dataclass (ticker, company_facts_available, financials_available, source). Added `ticker_evidence` tuple to `WeeklyReviewLoadResult`. Loader builds the universe from portfolio + watchlist tickers (cash excluded), deduplicates, sorts stably, tracks source (portfolio/watchlist/portfolio_and_watchlist).
- `atlas/weekly_review/render.py`: Section 8 now emits per-ticker `Evidence Gap [TICKER]` lines (not bulk list). Section 9 adds per-ticker follow-up questions. Section 10 adds per-ticker reasons to wait.
- `tests/test_weekly_review_evidence_presence_sprint219.py`: 42 new tests.
- `tests/test_weekly_review_trial_sprint213.py`: Two existing tests updated to match new per-ticker format.

**File convention:** `company_facts/<TICKER>.json` and `financials/<TICKER>.csv`. Ticker normalized to uppercase. Exact match. No fuzzy matching.

**Directory missing behavior:** Missing directories remain non-blocking. When directory is absent, no per-ticker gap lines are emitted (to avoid noise); the general "not loaded" note remains.

**Next sprint recommendation:** Sprint 220 — Run second real portfolio trial.

---

## 2026-07-03: Sprint 218 — Load Investor Profile Principles and Constraints into Weekly Review

Decision: Surface the user's stated principles and constraints directly in the Weekly Review output (Sections 5, 6, and 10) without invoking the suitability engine.

**Rationale:** After freezing the internal v1 release candidate, Atlas improves the local-only Weekly Review by surfacing the user's stated principles and constraints directly in the output. This strengthens process discipline without adding suitability scoring, provider dependencies, or recommendation behavior.

**Changes:**
- `atlas/weekly_review/inputs.py`: Added `invalid_profile_principles` and `invalid_profile_constraints` warnings when those fields exist but are not lists. Malformed fields produce empty tuples — no failure.
- `atlas/weekly_review/render.py`: Section 10 now surfaces each principle as a "Reason to Wait" and each constraint as "No Action Warranted". Sections 5 and 6 already rendered these fields; no change needed there.
- `tests/test_weekly_review_profile_context_sprint218.py`: 46 new focused tests.
- Docs updated.

**Profile parsing behavior:**
- `principles` field is a list → parsed into `profile_principles` tuple (stable order)
- `constraints` field is a list → parsed into `profile_constraints` tuple (stable order)
- Either field not a list → `invalid_profile_principles` / `invalid_profile_constraints` warning; empty tuple
- Profile file missing → `missing_optional_profile` warning; all profile fields empty
- Unknown profile fields ignored safely

**Next sprint recommendation:** Sprint 219 — Wire per-ticker company facts and financials presence checks more deeply into Missing Evidence and Follow-Up Questions.

---

## 2026-07-03: Sprint 217 — Internal v1 Release Candidate Freeze

Decision: Formally mark current state as the Atlas internal v1 release candidate and freeze the Weekly Review feature set.

**Rationale:** After 10 consecutive productization sprints (208–217), the Weekly Review workflow is stable, tested, documented, and verified against all guardrails. Freezing an RC baseline makes the boundary explicit before deeper engine wiring.

**Changes:**
- `atlas/__init__.py`: Added `__release_stage__ = "Internal v1 RC — Weekly Review (Sprint 217)"`
- `docs/InternalV1ReleaseCandidate.md`: Full RC definition with 24-item acceptance checklist (all ✓), included/excluded capabilities, command surface, guardrail acceptance, verification results, known limitations, productization track summary
- 16 new tests; 1970 total passing

**Acceptance result:** All 24 criteria met. Internal v1 RC status confirmed.

**Next sprint recommendation:** Sprint 218 — Load investor profile principles and constraints more deeply into Weekly Review (explicit guardrail checks in Section 6, relevant constraints in Section 10, without invoking the full suitability engine).

---

## 2026-07-03: Sprint 216 — Release Hardening Checkpoint for Weekly Review v1

Decision: Pause feature expansion for a release hardening checkpoint across Weekly Review sprints 209–215.

**Rationale:** After six productization sprints for Weekly Review, Atlas pauses feature expansion to verify local inputs, CLI behavior, renderer output, journal aging, usage documentation, guardrails, and provider-free boundaries before adding deeper engine wiring or new product surfaces.

**Fix found and applied:** `atlas/cli/main.py` still referenced `render_weekly_review_skeleton` (Sprint 211 alias) instead of `render_weekly_review`. Docstring also said "skeleton". Updated import and docstring — no behavioral change since the alias delegates to the same function.

**Verification results:**
- Minimal command: exit 0, all 10 sections, Section 10 non-empty ✓
- Full minimal-bundle command: exit 0, per-ticker missing facts/financials noted ✓
- Realistic command: exit 0, NESTE aging (473 days) flagged, 3 other entries clean ✓
- Provider boundary: clean ✓
- Language guardrails: clean ✓
- 7 closed cleanup deletion targets: all absent ✓
- 13 usage guide example paths: all present ✓
- Tests: 1954 passed, 3 skipped, RC2 green ✓

**New doc:** `docs/WeeklyReviewReleaseHardening.md` — full checkpoint record.

**Next sprint recommendation:** Sprint 217 — Release candidate freeze for internal v1. Mark current state as the internal v1 release candidate before further engine wiring.

---

## 2026-07-03: Sprint 215 — v1 Weekly Review Usage Guide

Decision: Create a practical v1 usage guide for `atlas weekly-review`.

**Rationale:** After implementing local inputs (Sprint 210), CLI (Sprint 211), renderer (Sprint 212), realistic trial (Sprint 213), and journal aging alerts (Sprint 214), the next highest-value step is to make the workflow usable by a real user without source-code knowledge. A practical guide reduces onboarding friction without expanding product scope.

**Guide created:** `docs/AtlasWeeklyReviewUsageGuide.md`

**Contents:** required/optional files, folder structure, portfolio/watchlist/profile/journal formats, command examples, all 10 output sections in user terms, Section 10 philosophy, journal aging behavior, common warnings, weekly update routine, current limitations.

**README updated:** Weekly Review added to capabilities table; pointer to usage guide added.

**Tests:** 26 tests in `tests/test_weekly_review_usage_guide_sprint215.py`. 1954 total passing. RC2 green.

**Next sprint recommendation:** Sprint 216 — Release hardening checkpoint across all Weekly Review sprints (209–215).

---

## 2026-07-03: Sprint 214 — Journal Entry Aging Alerts

Decision: Add deterministic aging detection for decision journal entries in the Weekly Investment Review.

**Rationale:** Decision journal entries older than 90 days are useful signals for thesis refresh and assumption review. Surfacing them in Open Decisions and Non-Actions / Reasons to Wait improves decision hygiene without creating recommendations, urgency, or live-data dependency.

**Aging rule:** entry age > 90 calendar days from `as_of` (strictly greater than). Requires `as_of` to be deterministic — no current-date dependency.

**Date field priority:** `decision_date`, `date`, `created_at`, `created`, `timestamp`, `review_date` (first valid field wins).

**Status filtering:** aging only fires for open entries. Closed-like statuses (`Closed`, `Archived`, `Completed`, `Resolved`) suppress alerts. Unknown statuses are treated as open (Unclassified).

**Section 7:** aged entries show `[Aging Note] {asset}: Review date is older than 90 days ({N} days). Thesis assumptions may need to be rechecked.` Open entries with no parseable date show `[Date Missing]` note.

**Section 10:** aged entries create: `Reason to Wait: {asset} decision journal notes are older than 90 days ({N} days). Assumptions should be refreshed before changing decision status.`

**What changed:** `atlas/weekly_review/render.py` — 5 new helper functions (`_parse_journal_entry_date`, `_is_journal_entry_open`, `_journal_entry_age_days`, `_is_aged_journal_entry`, `_render_journal_aging_note`), Section 7 aging note injection, Section 10 aged reason-to-wait injection.

**Test coverage:** 56 tests in `tests/test_weekly_review_journal_aging_sprint214.py`. 1928 total tests passing.

**Limitations:** No aging on missing `as_of`. No aging if date field is missing/invalid (renders safe note, does not fail). Financial/suitability engine not yet wired.

**Next sprint recommendation:** Sprint 215 — v1 usage guide.

---

## 2026-07-03: Sprint 213 — Run Real Portfolio Trial

Decision: Run `atlas weekly-review` on a realistic (anonymized) input bundle and make targeted improvements based on trial findings.

**Rationale:** The renderer from Sprint 212 was built against the minimal test bundle. A realistic trial (11 holdings, 5 watchlist items, full investor profile, decision journal, partial facts/financials) surfaces real usability issues before deeper engine integration.

**Improvements made:**
- Load investor profile principles/constraints/risk_tolerance/time_horizon into `WeeklyReviewLoadResult` (Sections 5+6 were nearly empty without these)
- Per-ticker company facts and financials presence check — replaces generic binary "facts loaded/not loaded" with actionable "Missing company facts for: LVMH, COLB, ..."
- `_preview_scope_notes()` helper strips markdown headers and inline syntax from scope notes (raw markdown was rendering in Section 1)
- Combined top-2 concentration note fires when top-2 non-cash holdings together exceed 40%
- Single-position concentration threshold lowered from >30% to >25%

**Trial bundle:** `examples/weekly_review_realistic/` — 11-holding portfolio, 5-item watchlist, full profile, 4 journal entries, 3/16 tickers with facts/financials.

**Test coverage:** 54 tests in `tests/test_weekly_review_trial_sprint213.py`. 1872 total tests passing.

**Findings documented:** `docs/WeeklyReviewTrialFindings.md`

**Next sprint recommendation:** Sprint 214 — Journal entry aging alerts. Flag journal entries older than 90 days in Sections 7 and 10. Small scope, high signal value.

---

## 2026-07-03: Sprint 212 — Implement Weekly Investment Review Renderer

Decision: Replace placeholder renderer content with deterministic output derived from the local `WeeklyReviewLoadResult`.

**Rationale:** After exposing the `atlas weekly-review` command (Sprint 211), Atlas needs useful output from the local input bundle before deeper engine orchestration. Rendering portfolio context, watchlist evidence gaps, open decisions, missing evidence, follow-up questions, and non-actions makes the workflow usable while preserving deterministic local-only behavior.

**Findings:**
- `render_weekly_review(result)` introduced in `atlas/weekly_review/render.py`; `render_weekly_review_skeleton` kept as backward-compatible alias — all Sprint 211 tests remain green
- `WeeklyReviewLoadResult.journal_entries: tuple[dict[str, Any], ...] = ()` added — lightweight raw dict read from journal JSON, zero-cost when journal absent; `journal_entry_count` preserved for backward compatibility
- Section 2: holdings sorted by weight descending (stable: secondary sort by ticker), sector % breakdown, concentration note, cash note
- Section 3: per-item watchlist detail — reason, evidence gaps, open questions, observations, notes
- Section 4: evidence-gap items (≥2 gaps), visible holdings (>20% weight), portfolio/watchlist overlap
- Section 5: profile availability, concentration observation, cash position, deferred engine note
- Section 6: elevated risk scores, missing cost basis, sector concentration, deferred engine note
- Section 7: per-entry decision title, status, first two follow-up triggers, atlas_view snippet
- Section 8: consolidated evidence gaps by ticker + missing optional input flags
- Section 9: watchlist open_questions + additional journal follow-up triggers + derived questions
- Section 10: deferred/needs-more-evidence items + evidence gap count + missing optional reasons + universal reminders (always non-empty)
- Forbidden language scan: 0 forbidden terms in full output with sample files
- Zero provider/network imports added
- 63 new tests | **1818 passed, 3 skipped | RC2 green | Demo passes ✓**

**Changes made:** Rewrote `atlas/weekly_review/render.py`. Extended `atlas/weekly_review/inputs.py` (`WeeklyReviewLoadResult.journal_entries`). Updated `atlas/weekly_review/__init__.py` (added `render_weekly_review`). Created `tests/test_weekly_review_renderer_sprint212.py`. Updated `docs/AtlasWeeklyInvestmentReviewSpec.md`, `docs/DecisionLog.md`, `docs/LegacyConsolidationPlan.md`, `docs/ArchitectureConsolidation.md`.

**Next sprint recommendation:** Sprint 213 — Run real portfolio trial. Once the renderer produces useful local-input-derived output, the fastest improvement path is to run `atlas weekly-review` on a realistic portfolio/watchlist/profile bundle and identify friction before wiring deeper engines.

---

## 2026-07-03: Sprint 211 — Implement Weekly Review CLI Skeleton

Decision: Add the `atlas weekly-review` command skeleton — the first end-to-end CLI surface for the Atlas Weekly Investment Review workflow.

**Rationale:** After implementing deterministic local input schemas (Sprint 210), Atlas exposes a minimal CLI surface that proves the Weekly Investment Review can load inputs end-to-end and render the required review structure without live data, provider calls, or recommendation language.

**Findings:**
- `atlas weekly-review` registered as root-level Typer command on `app` in `atlas/cli/main.py`
- Arguments: `--portfolio`/`--watchlist` required; `--profile`, `--journal`, `--company-facts`, `--financials`, `--as-of`, `--scope-notes` optional
- `atlas/weekly_review/render.py` created with `render_weekly_review_skeleton()` — returns string, no engine calls, no provider dependency
- Lazy import of `atlas.weekly_review` inside CLI command — avoids adding to module-level imports
- All 10 section headings present in output
- Section 10 (Non-Actions) always present and non-empty — includes deferred watchlist items
- Section 8 (Missing Evidence) populated from watchlist `evidence_needed` fields
- Missing required files → exit code 1 with clear error; missing optional → warning, not failure
- No forbidden language in output, help text, or renderer — confirmed by guardrail tests
- Zero provider/network imports in `render.py` or `__init__.py`
- All existing CLI commands remain available (verified by tests)
- 28 new tests | **1755 passed, 3 skipped | RC2 green | Demo passes ✓**

**Changes made:** Created `atlas/weekly_review/render.py`. Updated `atlas/weekly_review/__init__.py` (added `render_weekly_review_skeleton`). Added `weekly_review_command` to `atlas/cli/main.py`. Created `tests/test_weekly_review_cli_sprint211.py`. Updated `docs/AtlasWeeklyInvestmentReviewSpec.md`, `docs/DecisionLog.md`, `docs/LegacyConsolidationPlan.md`, `docs/ArchitectureConsolidation.md`.

**Next sprint recommendation:** Sprint 212 — Implement Weekly Investment Review renderer. Replace placeholder content with deterministic output derived from loaded inputs: portfolio summary, per-item watchlist review, open decisions from journal, consolidated evidence gaps, and non-actions from real data.

---

## 2026-07-03: Sprint 210 — Implement Local Input Schemas for Weekly Investment Review

Decision: Implement local input schemas for the Atlas Weekly Investment Review workflow as the first implementation step in the Atlas v1 productization track.

**Rationale:** Atlas v1 should use deterministic local files rather than live provider data, broker integrations, or external APIs. Implementing the portfolio, watchlist, profile, journal, and optional evidence input bundle creates the foundation for the future `atlas weekly-review` command. Getting inputs right first prevents rework in later sprints.

**Findings:**
- Created `atlas/weekly_review/` package at top level (matching `atlas/decision_journal/` and `atlas/watchlist_review/` conventions)
- `WeeklyReviewPortfolioInput`: supports both existing `positions[]` format and v1 extended `accounts[].holdings[]` format with market-value-derived weights and multi-account support
- `WeeklyReviewWatchlistInput`: full v1 rich item format with `status`, `evidence_needed`, `open_questions`, `manual_observations`, `notes`; legacy status alias mapping covers all existing `WatchlistStatus` enum values
- `WeeklyReviewInputWarning`: code + message, non-blocking; covers missing_optional_profile, missing_optional_journal, missing_optional_company_facts, missing_optional_financials, missing_sector, missing_watchlist_status, unknown_watchlist_status, invalid_journal
- `load_weekly_review_inputs()`: validates required files (fail), handles optional files (warn), returns `WeeklyReviewLoadResult`
- Decision journal: lightweight JSON read (entry count only) — avoids importing heavy `DecisionJournalEngine` in Sprint 210
- Profile: path forwarded + `profile_available` flag — full object loading deferred to Sprint 211
- Zero provider/network imports confirmed by guardrail test
- Sample files created: 7 files under `examples/weekly_review/` with placeholder data and safe language
- All 35 new tests pass | **1727 passed, 3 skipped | RC2 green | Demo passes ✓**

**Changes made:** Created `atlas/weekly_review/__init__.py`, `atlas/weekly_review/inputs.py`, `examples/weekly_review/` (7 files), `tests/test_weekly_review_inputs_sprint210.py`. Updated `docs/AtlasWeeklyInvestmentReviewSpec.md`, `docs/DecisionLog.md`, `docs/LegacyConsolidationPlan.md`, `docs/ArchitectureConsolidation.md`.

**Next sprint recommendation:** Sprint 211 — Implement `atlas weekly-review` command skeleton. Load inputs, validate, report warnings, print placeholder structure. No full orchestration yet.

---

## 2026-07-03: Sprint 209 — Specify Atlas Weekly Investment Review Workflow

Decision: Specify the Atlas Weekly Investment Review workflow as the flagship v1 workflow in sufficient detail for implementation.

**Rationale:** The Weekly Investment Review ties together company review, portfolio fit, suitability, watchlist review, risk/principle guardrails, decision history, missing evidence, and reasons to wait without requiring live data or recommendation language. Specifying it before implementing avoids ambiguity in later sprints and ensures the workflow respects all Atlas language and boundary guardrails.

**Findings:**
- Existing parsers that can be reused: `Portfolio.from_json_file`, `InvestorProfileEngine.load_profile`, `watchlist_review_input_from_json_file`, `DecisionJournalEngine.load_entries`
- Existing `WatchlistInput.from_mapping` accepts only `tickers` — does not support v1 rich watchlist format (gap)
- Existing `InvestorProfile` does not have `principles` or `constraints` fields (gap)
- No `company_facts/<ticker>.json` convention or parser exists (gap)
- No `atlas weekly-review` CLI command exists (gap)
- No multi-section Weekly Review renderer exists (gap)
- No "companies needing attention" orchestration engine exists (gap)
- No "non-actions" generator exists (gap)
- Sample data for weekly review does not exist in `examples/` (gap)
- All 8 v1 workflows map to existing active packages — no package deletion or creation needed
- 12 workflow steps specified, 10 output sections specified, CLI entrypoint designed
- Repository identity confirmed: Atlas only, no Atlas Edge naming encountered
- No runtime files changed | 1692 passed, 3 skipped | RC2 green | Demo passes ✓

**Changes made:** Created `docs/AtlasWeeklyInvestmentReviewSpec.md`. Updated `docs/AtlasV1OperatingMode.md`, `docs/DecisionLog.md`, `docs/LegacyConsolidationPlan.md`, `docs/ArchitectureConsolidation.md`.

**Next sprint recommendation:** Sprint 210 — Implement local input schemas for Weekly Investment Review. Create `examples/weekly_review/` sample files, new rich watchlist parser, `WeeklyReviewInput` loader with validation, and guardrail tests.

---

## 2026-07-03: Sprint 208 — Define Atlas v1 Operating Mode

Decision: Define the Atlas v1 product boundary, operating mode, and flagship workflow (Atlas Weekly Investment Review).

**Rationale:** After 25 closed cleanup tracks and repeated RC stability, Atlas has a clean, well-bounded codebase. Sprint 208 begins the productization track: defining what Atlas should do for the user, what it should never do, and what the canonical v1 workflow looks like. All 14 active packages were mapped to v1 roles. The Weekly Investment Review was selected as the flagship v1 workflow because it ties together company review, watchlist, suitability, risk/principles, open decisions, and missing evidence without requiring live data or recommendation language.

**Findings:**
- v1 product boundary defined: CLI-first, deterministic, local-only, long-term investor focus
- 8 candidate v1 workflows mapped against 14 active packages — all 8 included in v1
- Weekly Investment Review: flagship workflow, currently assembled manually from individual commands, no unified `atlas weekly-review` command yet
- Company Review, Decision Memo, Watchlist Review specifications written
- v1 input model: all local and file-based; no live data required
- v1 output model: 10 output types, all with explicit language guardrails
- Usable output criteria defined: evidence before opinion, reproducible, uncertainty stated, no recommendation language
- Out-of-scope list codified: live data, LLM conclusions, UI, broker integrations, Atlas Edge, price targets, buy/sell
- 10 guardrail principles for v1 and beyond
- **1692 passed, 3 skipped | RC2 green | Demo passes ✓**

**Changes made:** Created `docs/AtlasV1OperatingMode.md`. Updated `docs/DecisionLog.md`, `docs/LegacyConsolidationPlan.md`, `docs/ArchitectureConsolidation.md`.

**Next sprint recommendation:** Sprint 209 — Specify the Atlas Weekly Investment Review workflow. Full specification: input data structures, workflow steps, output section definitions, CLI entrypoint design, missing implementation gaps, implementation plan, acceptance criteria.

---

## 2026-07-03: Sprint 207 — Release Candidate Checkpoint Across 25 Closed Tracks

Decision: Confirm Atlas release-candidate stability across all 25 closed cleanup tracks after suitability cleanup closure.

**Rationale:** After closing the suitability cleanup track, Atlas remains stable. Suitability remains active, CLI-exposed, correctly bounded, provider-free, and free of recommendation-language issues. Removed modules remain absent, deleted modules remain absent, retired CLI paths remain retired, provider boundaries remain unchanged or intentionally classified, the demo remains provider-free, and release verification remains green.

**Findings:**
- All 25 closed cleanup tracks verified in documentation and repository ✓
- Sprint 206 suitability closure: `atlas/suitability/` unchanged — 7 exports all importable, `atlas suitability analyze` active, language clean, provider-free, no stale refs ✓
- Sprint 203 models closure: `Company` + `FinancialHistory` unchanged, `__all__ = ["Company", "FinancialHistory"]`, `investment_report.py` absent ✓
- Sprint 198/200 removals: all 5 targets remain absent — `investment_report.py`, `kpi_service.py`, `test_kpi_service.py`, `atlas/reports/`, `atlas/storage/` ✓
- Database/services: importable, `config ← database ← services ← CLI` boundary stable ✓
- 24 active packages importable in smoke test ✓
- 12 deleted modules confirmed absent ✓
- No stale active runtime references for any deleted/retired symbol ✓
- CLI: `atlas reason` non-callable, `evidence`/`reason`/`risk` groups absent, `atlas suitability analyze` active, all other active commands present ✓
- Provider boundaries unchanged or intentionally classified; `atlas/suitability/` provider-free ✓
- **1692 passed, 3 skipped | RC2 green | Demo passes ✓**

**Changes made:** Updated `docs/ReleaseCandidateCheckpoint.md` (Sprint 207 section, 25-track table, all verification tables). Updated `docs/DecisionLog.md`, `docs/LegacyConsolidationPlan.md`, `docs/ArchitectureConsolidation.md`.

**Next sprint recommendation:** Sprint 208 — Define Atlas v1 operating mode. After 25 closed cleanup tracks and repeated RC stability, begin a productization track to define what Atlas should do for the user on a daily or weekly basis.

---

## 2026-07-03: Sprint 206 — Close Suitability Cleanup Track

Decision: Formally close the `atlas/suitability/` cleanup track. No code changes.

**Rationale:** After inventory, export review, caller review, CLI suitability review, behavior review, boundary review, provider boundary review, recommendation-language guardrail review, closed-track guard, and overlap review, the suitability package contains only active, intentional application-layer suitability logic. Further cleanup would create churn without architectural benefit.

**Findings:**
- All Sprint 205 findings confirmed unchanged ✓
- `atlas/suitability/` — 2 modules, 642 lines — `__init__.py` + `engine.py` ✓
- 7 public exports all active: `OverallSuitability`, `SuitabilityAssessment`, `SuitabilityEngine`, `SuitabilityFactor`, `SuitabilityInput`, `SuitabilityMismatch`, `render_suitability_assessment` ✓
- 6 production callers unchanged: `atlas/cli/main.py`, `atlas/dashboard/engine.py`, `atlas/comparison/engine.py`, `atlas/watchlist_review/engine.py`, `atlas/portfolio_review/engine.py`, `atlas/risk_drift/engine.py` ✓
- `atlas suitability analyze` CLI command active, opt-in provider (default mock), no network calls ✓
- Output language clean — anti-advice disclaimer present; no buy/sell/recommendation/urgent language ✓
- `check_suitability_assessment` absent from active `atlas.suitability` exports ✓
- Engine imports: `atlas.analysis.engine`, `atlas.analysis.scores`, `atlas.capabilities.portfolio_intelligence`, `atlas.intelligence`, `atlas.profile`, `atlas.themes` — all correct consumer-pattern deps ✓
- No CLI, provider, database, services, or models imports in `atlas/suitability/` ✓
- No circular dependencies ✓
- No stale imports from any closed cleanup track ✓
- No overlap with decision/risk/principles/evidence — distinct application-layer package ✓
- **1692 passed, 3 skipped | RC2 green | Demo passes ✓**

**Changes made:** Updated `docs/SuitabilityCleanupPlan.md` (status CLOSED Sprint 206, Sprint 206 confirmation row, reopening condition). Updated `docs/DecisionLog.md`, `docs/LegacyConsolidationPlan.md`, `docs/ArchitectureConsolidation.md`.

**Next sprint recommendation:** Sprint 207 — Release candidate checkpoint across 25 closed cleanup tracks. After closing suitability as the 25th track, Atlas should run an RC checkpoint before the next broad audit, following the established RC pattern.

---

## 2026-07-03: Sprint 205 — Suitability Package Cleanup Checkpoint

Decision: Audit `atlas/suitability/` — no cleanup warranted. Sprint 206 target: close track.

**Rationale:** After inventory, export review, caller map, CLI review, behavior review, boundary review, provider boundary review, recommendation-language guardrail review, closed-track deletion guard, and overlap review, `atlas/suitability/` contains only active, intentional application-layer code. All 7 public exports have production callers. No stale exports, dead helpers, forbidden language, provider coupling, or stale references from closed cleanup tracks were found. The package is correctly bounded as a mid-layer engine that consumes analysis, intelligence, capability, profile, and theme inputs.

**Findings:**
- `atlas/suitability/` — 2 modules, 642 lines (`__init__.py` + `engine.py`) ✓
- 7 active public exports: `OverallSuitability`, `SuitabilityAssessment`, `SuitabilityEngine`, `SuitabilityFactor`, `SuitabilityInput`, `SuitabilityMismatch`, `render_suitability_assessment` — all with production callers ✓
- 6 production callers: CLI, dashboard, comparison, watchlist_review, portfolio_review, risk_drift ✓
- `atlas suitability analyze` CLI command — active, opt-in provider (default mock), no network calls ✓
- Output language — anti-advice disclaimer present (`"does not judge investment merit or provide personalized financial advice"`); no forbidden buy/sell/recommendation language ✓
- `check_suitability_assessment` not present in active `atlas.suitability` exports (correctly absent since Sprint 157) ✓
- Boundary: suitability → analysis/capability/intelligence/profile/themes; CLI/dashboard/comparison/watchlist_review/portfolio_review/risk_drift → suitability; no upward dep, no circular dep ✓
- Provider coupling: none in `atlas/suitability/` — provider access at CLI layer only (opt-in) ✓
- No stale imports from any closed cleanup track ✓
- No overlap with decision, risk, principles, or evidence — distinct application-layer package ✓
- **1692 passed, 3 skipped | RC2 green | Demo passes ✓**

**Changes made:** Created `docs/SuitabilityCleanupPlan.md`. Created `tests/test_suitability_sprint205.py` (11 guardrail tests). Updated `docs/DecisionLog.md`, `docs/LegacyConsolidationPlan.md`, `docs/ArchitectureConsolidation.md`.

**Next sprint recommendation:** Sprint 206 — Close suitability cleanup track (no cleanup warranted; Sprint 205 confirmed clean).

---

## 2026-07-03: Sprint 204 — Release Candidate Checkpoint Across 24 Closed Tracks

Decision: Confirm Atlas release-candidate stability across all 24 closed cleanup tracks after models cleanup closure.

**Rationale:** After closing the models cleanup track, Atlas remains stable. Models, database, and services ownership remains unchanged, removed modules remain absent, deleted modules remain absent, retired CLI paths remain retired, provider boundaries remain unchanged or intentionally classified, the demo remains provider-free, and release verification remains green.

**Findings:**
- All 24 closed cleanup tracks verified in documentation and repository ✓
- Sprint 203 models closure: `atlas/models/` unchanged — `Company` (10 cols), `FinancialHistory` (15 cols), `__all__ = ["Company", "FinancialHistory"]`, lazy shim clean, no `investment_report` reference ✓
- ORM/schema: `Base` in `atlas/database/connection.py`, schema creation in `database_service.py`, 6-table schema/ORM gap intentional ✓
- Sprint 198/200 removals: all 6 targets remain absent — `investment_report.py`, `kpi_service.py`, `test_kpi_service.py`, `reports/investment_card.py`, `atlas/reports/`, `atlas/storage/` ✓
- Database/services: all active symbols importable, `config ← database ← services ← CLI` boundary stable ✓
- 24 active packages importable in smoke test (note: `atlas.watchlist` top-level does not exist — watchlist surface in capabilities + adapters, confirmed Sprint 189/190) ✓
- 12 deleted modules confirmed absent ✓
- `atlas.analysis.__all__` remains 9 exports ✓
- `CompanyAnalysisProvider` — no standalone hits; all are `MockCompanyAnalysisProvider` substrings ✓
- CLI: 7 retired commands non-callable, empty CLI groups (`evidence`, `reason`, `risk`) absent from root help, all active commands present ✓
- Provider boundaries unchanged or intentionally classified; `atlas/watchlist_review/` coupling remains Outcome B (acceptable legacy coupling, Sprint 187) ✓
- **1681 passed, 3 skipped | RC2 green | Demo passes ✓**

**Changes made:** Updated `docs/ReleaseCandidateCheckpoint.md` (Sprint 204 section, 24-track table, all verification tables). Updated `docs/DecisionLog.md`, `docs/LegacyConsolidationPlan.md`, `docs/ArchitectureConsolidation.md`.

**Next sprint recommendation:** Sprint 205 — Audit `atlas/suitability/` package. Active, CLI-exposed, not yet audited.

---

## 2026-07-03: Sprint 203 — Close Models Cleanup Track

Decision: Formally close the `atlas/models/` cleanup track. No code changes.

**Rationale:** After inventory, ORM model review, lazy shim review, export review, caller review, models/database/services boundary review, database/schema boundary review, services usage review, provider boundary review, and stale import audit, the models package contains only active, intentional ORM/data-shape code. Further cleanup would create churn without architectural benefit.

**Findings:**
- All Sprint 202 findings confirmed unchanged ✓
- `atlas/models/__init__.py`: `__all__ = ["Company", "FinancialHistory"]`, lazy shim clean, no `investment_report` reference ✓
- `atlas/models/entities.py`: `Company` (9 cols, `companies` table) and `FinancialHistory` (13 cols, `financial_history` table) — both active, all columns unchanged ✓
- Production callers unchanged: `database_service.py`, `company_service.py`, `financial_import_service.py` ✓
- Zero imports of `atlas.models.investment_report` anywhere in repo ✓
- Boundary direction stable: models → database (Base), services → models — no upward dependency, no circular deps ✓
- Zero provider coupling, zero network access in `atlas/models/` ✓
- `atlas/models/investment_report.py`, `atlas/reports/`, `atlas/storage/` all confirmed absent ✓
- Zero stale imports from any closed cleanup track in `atlas/models/` ✓
- **1681 passed, 3 skipped | RC2 green | Demo passes ✓**

**Changes made:** Updated `docs/ModelsCleanupPlan.md` (closure sprint changed to Sprint 203, future reopening condition updated). Updated `docs/DecisionLog.md`, `docs/LegacyConsolidationPlan.md`, `docs/ArchitectureConsolidation.md`.

**Next sprint recommendation:** Sprint 204 — Release candidate checkpoint across 24 closed cleanup tracks. After closing models following config (Sprint 196), database/services (Sprint 198), and storage (Sprint 200), Atlas should run an RC checkpoint before the next broad audit.

---

## 2026-07-03: Sprint 202 — Models Package Cleanup Checkpoint

Decision: Confirm `atlas/models/` is clean and close the models cleanup track with no code changes.

**Rationale:** After Sprint 198 removed `atlas/models/investment_report.py` (dead re-export shim), the remaining surface (`entities.py`, `__init__.py`) had not had a dedicated audit. Sprint 202 audited both modules: 2 active ORM models, 3 production callers, lazy `__init__.py` shim with no stale references, correct boundary direction (models → database), zero provider coupling, zero stale imports from closed tracks. No cleanup warranted.

**Findings:**
- `atlas/models/__init__.py` (11 lines): lazy `__getattr__` shim, `__all__ = ["Company", "FinancialHistory"]`, no reference to removed `investment_report.py` ✓
- `atlas/models/entities.py` (41 lines): `Company(Base)` (9 cols + relationship) and `FinancialHistory(Base)` (13 cols + relationship + UniqueConstraint) — both active ✓
- Production callers: `database_service.py` (ORM registration), `company_service.py` (CRUD), `financial_import_service.py` (import pipeline) ✓
- `InvestmentReport` in active code all routed through `atlas.analysis.engine` — zero imports from deleted `atlas.models.investment_report` ✓
- Boundary direction correct: models import `Base` from `atlas.database.connection`, services import from models — no upward dependency, no circular deps ✓
- Two `Company` classes (`atlas.models.entities.Company` vs. `atlas.shared.Company`) are architecturally intentional — different layers ✓
- Schema/ORM gap (6 unmapped tables) is intentional and unchanged ✓
- Sprint 198 removals and Sprint 200 storage findings remain confirmed absent ✓
- **1671 passed, 3 skipped | RC2 green | Demo passes ✓**

**Changes made:** Created `docs/ModelsCleanupPlan.md`. Created `tests/test_models_sprint202.py` (guardrail tests). Updated `docs/DecisionLog.md`, `docs/LegacyConsolidationPlan.md`, `docs/ArchitectureConsolidation.md`.

**Next sprint recommendation:** Sprint 203 — Close models cleanup track (no cleanup warranted; Sprint 202 confirmed clean). Confirm findings unchanged, run final verification.

---

## 2026-07-03: Sprint 201 — Release Candidate Checkpoint Across 23 Closed Tracks

Decision: Confirm Atlas release-candidate stability across all 23 closed cleanup tracks after storage boundary closure.

**Rationale:** After confirming storage/persistence ownership and closing the storage boundary cleanup track in Sprint 200, Atlas remains stable. `atlas/storage/` confirmed non-existent with zero Python imports anywhere. Database and services ownership remains unchanged. Deleted modules remain absent. Retired CLI paths remain retired. Provider boundaries remain unchanged or intentionally classified. Demo remains provider-free. Release verification remains green.

**Findings:**
- All 23 closed cleanup tracks verified in documentation and repository ✓
- Sprint 200 storage boundary: `atlas/storage/` does not exist, zero `atlas.storage` imports, closure confirmed stable ✓
- Sprint 198 removals: all 5 targets remain absent ✓
- `atlas/reports/` absent — no follow-up needed ✓
- Database/services: all 8 active symbols importable, boundary stable ✓
- Config/database/services: config ← database ← services ← CLI — unchanged ✓
- SQLAlchemy/SQLite/schema: unchanged ✓
- 20 active packages importable in smoke test ✓
- 16 deleted modules confirmed absent ✓
- `CompanyAnalysisProvider` substring hits all match `MockCompanyAnalysisProvider` in intentional active code — no standalone stale reference ✓
- CLI: 7 retired commands non-callable, empty CLI groups absent, all active commands present ✓
- Provider boundaries unchanged or intentionally classified ✓
- **1671 passed, 3 skipped | RC2 green | Demo passes ✓**

**Changes made:** Updated `docs/ReleaseCandidateCheckpoint.md` (Sprint 201 section, 23-track table, all verification tables). Updated `docs/DecisionLog.md`, `docs/LegacyConsolidationPlan.md`, `docs/ArchitectureConsolidation.md`.

**Next sprint recommendation:** Sprint 202 — Audit `atlas/models/` package. After database/services and storage boundary closure and two RC checkpoints (Sprint 199, Sprint 201), `atlas/models/` is the next natural persistence/data-shape package to audit. Sprint 198 already removed `atlas/models/investment_report.py`; the remaining surface (`entities.py`, `__init__.py`) has not had a dedicated audit.

---

## 2026-07-03: Sprint 200 — Storage Boundary Cleanup Checkpoint

Decision: Close the storage boundary cleanup track. `atlas/storage/` does not exist. Storage and persistence behavior are fully owned by `atlas/database/` and `atlas/services/`. No cleanup warranted.

**Rationale:** Repo-wide search confirmed zero Python imports of `atlas.storage` anywhere in the codebase. `atlas/storage/` does not exist as a package, module, or placeholder. All five documentation references to `atlas/storage/` are historical confirmations that the package does not exist. Storage/persistence is cleanly owned by `atlas/database/` (SQLAlchemy ORM, connection, session, schema) and `atlas/services/` (init, CRUD, financial import). Config/database/services boundary remains stable. No stale imports from closed tracks. Sprint 198 removals confirmed absent.

**Final verified state:**
- `atlas/storage/` does not exist — classification: `nonexistent_storage_package` ✓
- Zero Python imports of `atlas.storage` anywhere ✓
- Storage/persistence ownership: `atlas/database/` + `atlas/services/` — complete and clean ✓
- Config/database/services boundary: config ← database ← services ← CLI — unchanged ✓
- SQLAlchemy/SQLite/schema behavior unchanged ✓
- Sprint 198 removals all confirmed absent ✓
- No provider coupling, no network access in storage/database/services ✓
- **1671 passed, 3 skipped | RC2 green | Demo passes ✓**

**Changes made:** Created `docs/StorageCleanupPlan.md` (CLOSED). Updated `docs/DecisionLog.md`, `docs/LegacyConsolidationPlan.md`, `docs/ArchitectureConsolidation.md`.

**Next sprint recommendation:** Sprint 201 — Release candidate checkpoint. After confirming the storage boundary and closing the 23rd cleanup track, Atlas should run a release candidate checkpoint before the next broad audit.

---

## 2026-07-03: Sprint 199 — Release Candidate Checkpoint Across 22 Closed Tracks

Decision: Confirm Atlas release-candidate stability across all 22 closed cleanup tracks after database/services dead symbol removal.

**Rationale:** After removing dead database/services-adjacent symbols (`kpi_service.py`, `atlas/models/investment_report.py`, `atlas/reports/investment_card.py`, `atlas/reports/` directory) and closing the database/services cleanup track in Sprint 198, Atlas remains stable. Database and services exports remain importable, schema/session behavior is unchanged, deleted modules remain absent, retired CLI paths remain retired, provider boundaries remain unchanged or intentionally classified, the demo remains provider-free, and release verification remains green.

**Findings:**
- All 22 closed cleanup tracks verified in documentation and repository ✓
- Sprint 198 removals confirmed stable: 4 deleted targets remain absent ✓
- `atlas/reports/` deleted and absent — no callers, no follow-up needed ✓
- Database/services exports all importable: `Base`, `get_engine`, `get_session`, `init_database`, `add_company`, `list_companies`, `get_company_by_ticker`, `import_financials` ✓
- Config/database/services boundary correct throughout ✓
- SQLAlchemy/SQLite/schema behavior unchanged ✓
- Active services behavior unchanged (3 service modules, all active) ✓
- 21 packages importable in smoke test ✓
- 16 deleted modules/packages confirmed absent ✓
- CLI: 7 retired commands non-callable, empty CLI groups absent, all active commands present ✓
- Provider boundaries unchanged or intentionally classified ✓
- **1671 passed, 3 skipped | RC2 green | Demo passes ✓**

**Changes made:** Updated `docs/ReleaseCandidateCheckpoint.md` (Sprint 199 section, 22-track table, all verification tables). Updated `docs/DecisionLog.md`, `docs/LegacyConsolidationPlan.md`, `docs/ArchitectureConsolidation.md`.

**Next sprint recommendation:** Sprint 200 — Audit `atlas/storage/` package. After config and database/services are clean and closed, `atlas/storage/` is the natural next infrastructure boundary to audit before deeper runtime or model cleanup.

---

## 2026-07-03: Sprint 198 — Remove Database/Services Dead Symbols and Close Track

Decision: Remove three zero-caller dead symbols identified during the Sprint 197 database/services audit, delete the now-empty `atlas/reports/` directory, and close the database/services cleanup track.

**Rationale:** All three targets had zero production callers confirmed by repo-wide search before removal. `kpi_service.py` was a pure math utility never wired into any production pipeline. `atlas/models/investment_report.py` was a dead re-export shim. `atlas/reports/investment_card.py` was a dead function. `atlas/reports/` had no `__init__.py` and became empty after removal — deleted safely with zero callers. No runtime, database, service, provider, or CLI behavior changed.

**Actions taken:**
- Deleted `atlas/services/kpi_service.py` (zero production callers)
- Deleted `tests/test_kpi_service.py` (test for deleted dead module)
- Deleted `atlas/models/investment_report.py` (zero callers anywhere)
- Deleted `atlas/reports/investment_card.py` (zero callers anywhere)
- Deleted `atlas/reports/` directory (empty after removal, no callers, no `__init__.py`)
- Updated `tests/test_database_services_sprint197.py` — Sprint 197 "still present" stubs replaced with Sprint 198 absence guards

**Final verified state:**
- `atlas/services/` now 3 modules: `database_service.py`, `company_service.py`, `financial_import_service.py` — all active ✓
- `atlas/models/` retains `entities.py` + `__init__.py` — all active ✓
- `atlas/reports/` no longer exists ✓
- All active database, services, models, CLI symbols unchanged ✓
- No provider coupling, no network access ✓
- Boundary direction: config ← database ← services ← CLI — unchanged ✓
- **1671 passed, 3 skipped | RC2 green | Demo passes ✓**

**Changes made:** Deleted 4 files, 1 directory. Updated `tests/test_database_services_sprint197.py`. Updated `docs/DatabaseServicesCleanupPlan.md` (CLOSED). Updated standard docs.

**Next sprint recommendation:** Sprint 199 — Release candidate checkpoint. After closing the database/services cleanup track (Sprint 198, 22nd closed track) following dead symbol removal, a release checkpoint is warranted before the next broad audit.

---

## 2026-07-03: Sprint 197 — Audit Database and Services Packages

Decision: Confirm that `atlas/database/` and `atlas/services/` are clean, well-bounded, and contain three zero-caller dead code items to remove in Sprint 198. No cleanup made this sprint — audit-only.

**Rationale:** `atlas/database/` (1 module, 20 lines) and `atlas/services/` (4 modules, 164 lines) are the persistence infrastructure and orchestration layer for Atlas. All database and service symbols have correct production callers, correct boundary directions (config ← database ← models ← services ← CLI), no provider coupling, no network access, and no stale imports from any closed cleanup track. Three adjacent dead-code items were discovered during caller-map analysis: `atlas/services/kpi_service.py` (zero production callers — test-only pure math utility), `atlas/models/investment_report.py` (dead re-export shim, zero callers), `atlas/reports/investment_card.py` (dead function, zero callers). The schema/ORM gap (6 of 8 schema.sql tables have no ORM model) is intentional and not a bug.

**Final verified state:**
- `atlas/database/connection.py` (20 lines): `Base`, `get_engine`, `get_session` — all active, all callers confirmed ✓
- `atlas/database/schema.sql`: 8 tables; 2 have ORM models, 6 do not (intentional) ✓
- `atlas/services/database_service.py` (19 lines): `init_database` — active, called by CLI `atlas init` ✓
- `atlas/services/company_service.py` (43 lines): `add_company`, `list_companies`, `get_company_by_ticker` — all active ✓
- `atlas/services/financial_import_service.py` (86 lines): `import_financials` — active, called by CLI ✓
- `atlas/services/kpi_service.py` (16 lines): zero production callers — **cleanup candidate Sprint 198** ✓
- `atlas/models/investment_report.py` (3 lines): zero callers — **cleanup candidate Sprint 198** ✓
- `atlas/reports/investment_card.py` (23 lines): zero callers — **cleanup candidate Sprint 198** ✓
- No provider coupling in database or services ✓
- No network access ✓
- No stale imports from closed cleanup tracks ✓
- Boundary direction: config ← database ← services ← CLI — correct ✓
- `atlas/storage/` does not exist ✓
- **1654 passed, 3 skipped | RC2 green | Demo passes ✓**

**Changes made:** Created `docs/DatabaseServicesCleanupPlan.md`. Created `tests/test_database_services_sprint197.py` (guardrail tests). Updated `docs/DecisionLog.md`, `docs/LegacyConsolidationPlan.md`, `docs/ArchitectureConsolidation.md`.

**Next sprint recommendation:** Sprint 198 — Remove zero-caller dead code discovered during database/services audit: delete `atlas/services/kpi_service.py` + `tests/test_kpi_service.py`, `atlas/models/investment_report.py`, and `atlas/reports/investment_card.py` (and `atlas/reports/` directory if empty after removal). Then close the database/services cleanup track.

---

## 2026-07-03: Sprint 196 — Close Config Cleanup Track

Decision: Close the `atlas/config/` cleanup track. Sprint 196 confirmed all Sprint 195 findings unchanged — no cleanup warranted.

**Rationale:** After inventory, export review, caller review, configuration/provider/runtime boundary review, provider boundary review, runtime defaults review, environment/file loading review, storage/database/services boundary review, and stale import audit, the config package contains only active, intentional infrastructure code. `atlas/config.py` is 6 lines, stdlib-only, with zero Atlas imports, zero provider coupling, zero network access, and 2 active production callers. Further cleanup would create churn without architectural benefit.

**Final verified state:**
- `atlas/config.py` exists, 6 lines, unchanged ✓
- 3 public constants: `DATABASE_PATH` (2 active callers), `BASE_DIR` and `DATABASE_DIR` (internal derivations) ✓
- `ATLAS_HOME` env var: unchanged; covered by `test_atlas_home_env_var_respected` ✓
- No Atlas package imports ✓
- No provider imports ✓
- No network access ✓
- No stale imports from closed cleanup tracks ✓
- Boundary direction: config ← database ← services ← CLI — correct ✓
- `atlas/storage/` does not exist; storage layer is `atlas/database/` + `atlas/services/` ✓
- **1654 passed, 3 skipped | RC2 green | Demo passes ✓**

**Changes made:** Marked `docs/ConfigCleanupPlan.md` CLOSED with Sprint 196 section and verification table. Updated standard docs.

**Next sprint recommendation:** Audit `atlas/database/` and `atlas/services/` together (Sprint 197) — the two packages that consume `atlas/config.py` directly. Understanding the database/services layer is the logical next step.

---

## 2026-07-03: Sprint 195 — Audit Config Package

Decision: Confirm that `atlas/config.py` (the Atlas configuration layer) is clean, well-bounded, and requires no cleanup. Note that `atlas/config/` does not exist as a package directory — the configuration surface is a single 6-line module at `atlas/config.py`.

**Rationale:** `atlas/config.py` is foundational infrastructure at its simplest: one environment variable read (`ATLAS_HOME`), three derived path constants (`BASE_DIR`, `DATABASE_DIR`, `DATABASE_PATH`), stdlib-only imports, zero Atlas package imports, zero provider coupling, zero network access, 2 active production callers (both in the database/services layer). Boundary direction is correct — config depends on nothing within Atlas. All boundaries are clean. No stale imports. No dead symbols.

**Final verified state:**
- `atlas/config.py` exists (single-file module, 6 lines) ✓
- 3 public path constants: `BASE_DIR`, `DATABASE_DIR`, `DATABASE_PATH` ✓
- `DATABASE_PATH` has 2 active production callers ✓
- `BASE_DIR` and `DATABASE_DIR` are internal derivations only (no external callers) ✓
- `ATLAS_HOME` env var: single configuration knob, deterministic fallback to `Path.cwd()` ✓
- No Atlas package imports ✓
- No provider imports ✓
- No network access ✓
- No stale imports from closed cleanup tracks ✓
- No circular dependencies ✓
- `atlas/storage/` package does not exist; storage layer is `atlas/database/` + `atlas/services/` ✓
- Boundary direction correct: config ← database ← services ← CLI ✓
- **1654 passed, 3 skipped | RC2 green | Demo passes ✓**
- Suite growth since Sprint 194: 1648 → 1654 (+6 config guardrail tests)

**Changes made:** Created `docs/ConfigCleanupPlan.md`. Created `tests/test_config_sprint195.py` (6 guardrail tests). Updated `docs/LegacyConsolidationPlan.md`, `docs/ArchitectureConsolidation.md`, `docs/DecisionLog.md`.

**Next sprint recommendation:** Close config cleanup track (Sprint 196).

---

## 2026-07-03: Sprint 194 — Release Candidate Checkpoint After Residual Analysis Closure

Decision: Confirm Atlas release-candidate stability across all 21 closed cleanup tracks after the residual analysis public export reduction (Sprint 193: `atlas.analysis.__all__` reduced from 12 to 9 core exports).

**Rationale:** After closing the active residual analysis runtime track and removing 3 zero-caller provider re-exports from `atlas.analysis.__all__`, Atlas remains stable. All 9 remaining exports are importable and have active callers. Deleted modules remain absent. Retired CLI paths remain retired. Provider boundaries remain unchanged or intentionally classified. The demo remains provider-free. Release verification remains green.

**Final verified state:**
- 21 closed cleanup tracks — all stable ✓
- Residual analysis track CLOSED Sprint 193: `__all__` 12→9; 3 zero-caller provider re-exports removed ✓
- All 9 active `atlas.analysis.__all__` exports importable ✓
- `CompanyDataProvider`, `MockCompanyAnalysisProvider`, `YahooFinanceProvider` absent from `atlas.analysis.__all__` ✓
- `MockCompanyAnalysisProvider` shim in `company_analysis.py` active — 4 test callers ✓
- 13 deleted modules absent ✓
- 7 retired CLI commands non-callable ✓
- Empty CLI groups (`evidence`, `reason`, `risk`) absent from `atlas --help` ✓
- 18 active packages importable ✓
- Provider boundaries unchanged or intentionally classified ✓
- No stale active runtime references found ✓
- **1648 passed, 3 skipped | RC2 green | Demo passes ✓**
- Suite growth since Sprint 191 RC: 1637 → 1648 (+11 tests)

**Changes made:** Updated `docs/ReleaseCandidateCheckpoint.md` (Sprint 194 section: residual analysis closure verification, 21-track closed-track table, deleted module guard, CLI verification, 18-package smoke table, provider boundary table with Sprint 193 note, RC verification). Updated standard docs.

**Next sprint recommendation:** Audit `atlas/config/` package (Sprint 195).

---

## 2026-07-03: Sprint 193 — Close Residual Analysis Cleanup Track

Decision: Close the active residual `atlas/analysis/` cleanup track preserved by Sprint 141, and remove 3 zero-caller provider re-exports from `atlas/analysis/__init__.py`.

**Rationale:** Sprint 192 audited the surviving analysis residual surface and found it clean, well-bounded, and stable. Sprint 193 confirmed findings unchanged and completed the one eligible cleanup: removing `CompanyDataProvider`, `MockCompanyAnalysisProvider`, and `YahooFinanceProvider` from `atlas/analysis/__init__.py` and `__all__`. All 3 had zero callers from the package root — all actual callers import from `atlas.providers` or submodules directly. Removal changes the public re-export surface only; provider selection behavior remains unchanged at `atlas/cli/main.py` via `_provider_from_name()`. This is not a reopening of Sprint 141.

**Final verified state:**
- 5 surviving modules unchanged ✓
- `__all__` reduced from 12 to 9 (3 zero-caller provider re-exports removed) ✓
- All 9 remaining exports active and importable ✓
- `CompanyDataProvider`, `MockCompanyAnalysisProvider`, `YahooFinanceProvider` not in `atlas.analysis.__all__` ✓
- `MockCompanyAnalysisProvider` shim in `company_analysis.py` active — 4 test callers ✓
- `clamp_score` shared utility — 11 active callers across 11 packages ✓
- `atlas.analysis` → `atlas.capabilities.company_analysis`: absent ✓
- `atlas.capabilities.company_analysis` → `atlas.analysis`: absent ✓
- `atlas.domains` → `atlas.analysis`: absent ✓
- Sprint 141 deleted modules: all absent ✓
- No stale imports from deleted modules ✓
- No network access ✓
- No runtime behavior changed ✓
- **1648 passed, 3 skipped | RC2 green | Demo passes ✓**
- Suite growth since Sprint 192: 1647 → 1648 (+1 test)

**Changes made:** Edited `atlas/analysis/__init__.py` (removed 3 provider re-exports, `__all__` 12→9). Updated `tests/test_analysis_residual_sprint192.py` (export count updated, 3 absence assertions added). Updated `tests/test_analysis_package_sprint140.py` (export count and expected set updated). Marked `docs/AnalysisResidualCleanupPlan.md` CLOSED with Sprint 193 section. Updated standard docs.

**Next sprint recommendation:** Release candidate checkpoint (Sprint 194) — after closing the residual analysis track and changing the public re-export surface, Atlas should run a full RC checkpoint before the next broad audit.

---

## 2026-07-03: Sprint 192 — Audit Analysis Residual Surface

Decision: Confirm that the `atlas/analysis/` active residual runtime surface preserved by Sprint 141 is clean, well-bounded, and requires no urgent cleanup. Sprint 192 is not a reopening of the Sprint 141 main analysis cleanup track.

**Rationale:** The surviving analysis surface (5 modules, 652 lines, 12 active `__all__` exports) powers `atlas report`, `atlas analyze`, comparison, decision, monitoring, and suitability pipelines. All exports have production callers. No stale imports from deleted modules. Clean bidirectional boundary with `atlas/capabilities/company_analysis/`. No network access. Provider coupling is correct (engine receives provider as argument; selection is CLI-layer-only). One low-priority finding: 3 provider re-exports in `atlas/analysis/__init__.py` (`CompanyDataProvider`, `MockCompanyAnalysisProvider`, `YahooFinanceProvider`) have zero callers from the package root — all actual callers import from `atlas.providers` or submodules directly.

**Final verified state:**
- 5 surviving modules, 652 lines ✓
- 12 `__all__` exports — all active ✓
- `clamp_score` shared utility — 11 active callers across 11 packages ✓
- `atlas.analysis` → `atlas.capabilities.company_analysis`: absent ✓
- `atlas.capabilities.company_analysis` → `atlas.analysis`: absent ✓
- `atlas.domains` → `atlas.analysis`: absent ✓
- Sprint 141 deleted modules: all absent ✓
- No stale imports from deleted modules ✓
- No network access ✓
- `MockCompanyAnalysisProvider` shim active — 4 test callers ✓
- `CompanyAnalysisProvider` absent from active namespace ✓
- One cleanup candidate: 3 zero-caller provider re-exports in `__init__.py` (low priority)
- **1647 passed, 3 skipped | RC2 green | Demo passes ✓**
- Suite growth since Sprint 191: 1637 → 1647 (+10 tests)

**Changes made:** Created `docs/AnalysisResidualCleanupPlan.md`. Created `tests/test_analysis_residual_sprint192.py` (10 guardrail tests). Updated `docs/LegacyConsolidationPlan.md`, `docs/ArchitectureConsolidation.md`, `docs/DecisionLog.md`.

**Next sprint recommendation:** Close residual analysis cleanup track (Sprint 193).

---

## 2026-07-03: Sprint 191 — Release Candidate Checkpoint Across 20 Closed Tracks

Decision: Confirm Atlas release-candidate stability across all 20 closed cleanup tracks after three consecutive closures: `atlas/decision_journal/` (Sprint 185), `atlas/watchlist_review/` (Sprint 187), and `atlas/watchlist/` (Sprint 190).

**Rationale:** After closing decision journal, watchlist review, and watchlist, Atlas remains stable across all closed cleanup tracks. Active package exports remain importable, deleted modules remain absent, retired CLI paths remain retired, provider boundaries remain unchanged or intentionally classified, the demo remains provider-free, and release verification remains green.

**Final verified state:**
- 20 closed cleanup tracks — all stable ✓
- `atlas/decision_journal/` CLOSED Sprint 185 — 11 exports active, all callers valid ✓
- `atlas/watchlist_review/` CLOSED Sprint 187 — 11 exports active, provider coupling: acceptable legacy coupling ✓
- `atlas/watchlist/` CLOSED Sprint 190 — 13 capability exports active, adapter functions active, provider-free ✓
- 13 deleted modules remain absent ✓
- 7 retired CLI commands remain non-callable ✓
- `evidence`, `reason`, `risk` groups absent from `atlas --help` ✓
- 18 active packages importable ✓
- Provider boundaries unchanged or intentionally classified ✓
- Watchlist review provider boundary: Outcome B (acceptable legacy coupling, unchanged since Sprint 187) ✓
- `CompanyAnalysisProvider` absent from all active code ✓
- **1637 passed, 3 skipped | RC2 green | Demo passes ✓**
- Suite growth since Sprint 188 RC: 1622 → 1637 (+15 tests)

**Changes made:** Updated `docs/ReleaseCandidateCheckpoint.md` (Sprint 191 section: recent closure verification, watchlist review provider boundary, 20-track closed-track table, deleted module guard, CLI verification, 18-package smoke table, provider boundary table, RC verification). Updated standard docs.

**Next sprint recommendation:** Audit `atlas/analysis/` active residual surface (Sprint 192).

---

## 2026-07-03: Sprint 190 — Close Watchlist Cleanup Track

Decision: Close the Atlas watchlist cleanup track. After inventory, export review, caller review, watchlist/watchlist-review boundary review, evidence/decision/watchlist boundary review, provider boundary review, persistence/data shape review, and stale import audit, the watchlist package contains only active, intentional code. Further cleanup would create churn without architectural benefit.

**Rationale:** Sprint 190 confirmed all Sprint 189 findings unchanged. The watchlist surface (`atlas/capabilities/watchlist_intelligence/` + `atlas/adapters/watchlist.py`) is Blueprint-aligned, provider-free, stale-import-free, and boundary-correct. All 13 capability exports have active production callers. Both adapter functions have active production callers. Eleven production files consume watchlist types correctly. Boundary directions are correct throughout: watchlist_review consumes capability types; capability does not import watchlist_review. No dead code. No stale imports. No provider coupling.

**Final verified state:**
- `atlas/capabilities/watchlist_intelligence/` — 13 exports, all active, 11 production callers ✓
- `atlas/adapters/watchlist.py` — 2 public functions, both active ✓
- No stale imports from deleted modules ✓
- No provider coupling in capability or adapter ✓
- No CLI coupling in capability or adapter ✓
- No upward dependency on atlas.watchlist_review ✓
- `atlas/analysis/watchlist.py` remains deleted (Sprint 101) ✓
- `WatchlistEngine` remains absent (Sprint 99) ✓
- `CompanyAnalysisProvider` remains absent from atlas.analysis.company_analysis ✓
- All Sprint 189 guardrail tests (15) passing ✓
- **1637 passed, 3 skipped | RC2 green | Demo passes ✓**

**Changes made:** Updated `docs/WatchlistCleanupPlan.md` (status CLOSED, Sprint 190 closure verification table added). Updated `docs/LegacyConsolidationPlan.md`, `docs/ArchitectureConsolidation.md`, `docs/DecisionLog.md`. No new tests added — Sprint 189 guardrails (15 tests) provide full closure coverage.

**Next sprint recommendation:** Release candidate checkpoint (Sprint 191) — after closing the watchlist cleanup track adjacent to watchlist_review, Atlas should confirm release-candidate stability before the next broad audit.

---

## 2026-07-03: Sprint 189 — Watchlist Package Audit

Decision: Confirm that the Atlas watchlist surface requires no cleanup. No standalone `atlas/watchlist/` package exists. Watchlist functionality is distributed across `atlas/capabilities/watchlist_intelligence/` (4 modules, 545 lines, 13 exports) and `atlas/adapters/watchlist.py` (198 lines, 2 public functions). Both are Blueprint-aligned, provider-free, stale-import-free, and boundary-correct.

**Rationale:** The watchlist surface is among the most architecturally correct in the codebase. All 13 capability exports have active production callers. Both adapter functions have active production callers. The capability has no provider coupling (cleaner than watchlist_review which has acceptable legacy coupling). No upward dependency on watchlist_review. Legacy `atlas/analysis/watchlist.py` remains deleted (Sprint 101). `WatchlistEngine` remains absent (Sprint 99). Boundary direction is correct throughout: watchlist_review consumes capability types, not vice versa.

**Final verified state:**
- `atlas/watchlist/` standalone package: does not exist (correct — watchlist is a capability, not a legacy package) ✓
- `atlas/capabilities/watchlist_intelligence/` — 13 exports, all active ✓
- `atlas/adapters/watchlist.py` — 2 public functions, both active ✓
- No stale imports from deleted modules ✓
- No provider coupling in capability or adapter ✓
- No CLI coupling in capability or adapter ✓
- No upward dependency on atlas.watchlist_review ✓
- `atlas/analysis/watchlist.py` remains deleted ✓
- `CompanyAnalysisProvider` remains absent from atlas.analysis.company_analysis ✓
- **1637 passed, 3 skipped | RC2 green | Demo passes ✓**
- Suite growth since Sprint 188: 1622 → 1637 (+15 tests)

**Changes made:** Created `docs/WatchlistCleanupPlan.md`. Created `tests/test_watchlist_package_sprint189.py` (15 guardrail tests). Updated `docs/LegacyConsolidationPlan.md`, `docs/ArchitectureConsolidation.md`, `docs/DecisionLog.md`.

**Next sprint recommendation:** Close watchlist cleanup track (Sprint 190).

---

## 2026-07-03: Sprint 188 — Release Candidate Checkpoint

Decision: Confirm Atlas release-candidate stability after closing `atlas/decision_journal/` (Sprint 185) and `atlas/watchlist_review/` (Sprint 187).

**Rationale:** After closing two focused cleanup tracks, Atlas remains stable. All 17 closed cleanup tracks + company analysis residual cleanup are documented consistently. Decision journal and watchlist review closure states are verified unchanged. Watchlist review provider coupling remains classified as acceptable legacy coupling. Deleted modules remain absent. Retired CLI commands remain non-callable. Empty CLI groups remain absent from root help. 17 active packages remain importable. Demo is provider-free. Release verification is green.

**Final verified state:**
- 17 closed cleanup tracks + residual cleanup — all stable ✓
- `atlas/decision_journal/` CLOSED Sprint 185 — 11 exports active, all callers valid ✓
- `atlas/watchlist_review/` CLOSED Sprint 187 — 11 exports active, provider coupling: acceptable legacy coupling ✓
- 13 deleted modules remain absent ✓
- 7 retired CLI commands remain non-callable ✓
- `evidence`, `reason`, `risk` groups absent from `atlas --help` ✓
- 17 active packages importable ✓
- Provider boundaries unchanged ✓
- **1622 passed, 3 skipped | RC2 green | Demo passes ✓**
- Suite growth since Sprint 181 RC: 1598 → 1622 (+24 tests)

**Changes made:** Updated `docs/ReleaseCandidateCheckpoint.md` (Sprint 188 section: decision journal verification, watchlist review verification, provider boundary verification, closed-track table, deleted module guard, CLI verification, active package smoke, provider boundary table, RC verification). Updated standard docs.

**Next sprint recommendation:** Audit `atlas/watchlist/` package.

---

## 2026-07-03: Sprint 187 — Resolve Watchlist Review Provider Boundary

Decision: Classify `atlas/watchlist_review/engine.py` provider coupling as acceptable legacy coupling. No code change. Declare `atlas/watchlist_review/` cleanup track CLOSED.

**Rationale:** Sprint 187 assessed all decoupling options for the `from atlas.providers import CompanyDataProvider, MockCompanyAnalysisProvider` import in `engine.py`:

- **`CompanyDataProvider`** is already a `Protocol` in `atlas/providers/base.py` — its import is type-only with zero runtime effect. Creating a local duplicate protocol would add complexity for no architectural gain.
- **`MockCompanyAnalysisProvider()`** is instantiated as the deterministic default in 3 locations. Removing it would change the `WatchlistReviewEngine` API from "works with no configuration" to "requires explicit provider injection" — a behavior change not permitted in Sprint 187.
- **Pattern is codebase-consistent:** `atlas/cli/main.py:100` and `atlas/home/engine.py:32` both use the identical `from atlas.providers import CompanyDataProvider, MockCompanyAnalysisProvider` pattern. The coupling is not a unique anomaly in `watchlist_review/engine.py`; it is the established codebase pattern.
- **No circular dependency, no network access, no stale imports.**

All four decoupling options (structural protocol, loose type hint, move defaults outward, accept coupling) were evaluated. Option D is the only one that preserves behavior and API contracts without adding complexity.

**Final verified state:**
- 2 modules, 894 lines, 11 active exports — all importable ✓
- Provider coupling: `CompanyDataProvider` (Protocol, type-only) + `MockCompanyAnalysisProvider` (deterministic default) — acceptable legacy coupling ✓
- Active CLI: `atlas watchlist review` ✓
- Active application callers: `atlas/home/engine.py`, `atlas/conversation/engine.py` ✓
- No stale imports from any closed cleanup track ✓
- Deferred engine deletion note in `atlas/cli/deprecations.py` refers to `atlas.evidence` — still accurate ✓
- 1622 passed, 3 skipped | RC2 green | Demo passes ✓

**Changes made:** No code change to `engine.py`. Updated `tests/test_watchlist_review_package_sprint186.py` (guardrail docstring updated to reflect Sprint 187 classification). Updated `docs/WatchlistReviewCleanupPlan.md` (status CLOSED, Sprint 187 full resolution section including option analysis, deferred deletion verification, closure table).

**Next sprint recommendation:** Release candidate checkpoint.

---

## 2026-07-03: Sprint 186 — Watchlist Review Package Audit

Decision: Audit `atlas/watchlist_review/` and identify provider boundary as the primary cleanup candidate.

**Rationale:** Sprint 186 performed a full inventory of `atlas/watchlist_review/`. The package is active, with 2 modules (894 lines), 11 exports, CLI caller (`atlas watchlist review`), and application callers (`atlas/home/engine.py`, `atlas/conversation/engine.py`). One cleanup candidate was identified: `atlas.providers` is directly imported in `engine.py` — a non-adapter, non-CLI module — making `watchlist_review` the only legacy engine in the audited sequence that directly imports provider types outside the adapter layer. This is documented as a provider boundary issue. The deprecation note in `atlas/cli/deprecations.py` refers to `atlas.evidence` engine deletion deferral, not `atlas/watchlist_review` engine deletion — the note is still accurate.

**Key findings:**
- 2 modules, 894 lines, 11 active exports — all importable ✓
- Active CLI: `atlas watchlist review` ✓
- Active application callers: `atlas/home/engine.py`, `atlas/conversation/engine.py` ✓
- 10 lateral dependencies — all intentional, all runtime-active ✓
- **Provider boundary issue:** `engine.py:38` — `from atlas.providers import CompanyDataProvider, MockCompanyAnalysisProvider` — direct provider import in a non-adapter, non-CLI module ⚠
- No stale imports from any closed cleanup track ✓
- `WatchlistEngine` correctly absent (Sprint 94 guardrail) ✓
- Deprecation note accurately describes `atlas.evidence` engine deletion deferral, not `atlas/watchlist_review` deletion ✓
- 1614 passed, 3 skipped | RC2 green | Demo passes ✓

**Changes made:** Created `docs/WatchlistReviewCleanupPlan.md`. Added 8 Sprint 186 guardrail tests in `tests/test_watchlist_review_package_sprint186.py`. Updated standard docs.

**Next sprint recommendation:** Sprint 187 — assess and resolve the provider boundary issue (decouple or classify as acceptable legacy coupling and close the track).

---

## 2026-07-03: Sprint 185 — Close Decision Journal Cleanup Track

Decision: Declare `atlas/decision_journal/` cleanup track CLOSED.

**Rationale:** After inventory, export review, CLI and application caller review, evidence/decision boundary review, provider boundary review, persistence/data shape review, and stale import audit (Sprint 184), the decision journal package contains only active, intentional code. Sprint 185 confirmed all Sprint 184 findings unchanged. Further cleanup would create churn without architectural benefit.

**Final verified state:**
- 2 modules, 605 lines, 11 active exports — all importable ✓
- Active CLI callers: `atlas journal create`, `atlas journal list`, `atlas journal review` ✓
- Active application caller: `atlas/home/engine.py` (journal reminder logic) ✓
- 4 lateral dependencies (`atlas.evidence`, `atlas.language`, `atlas.principles`, `atlas.profile`) — all intentional, all runtime-active ✓
- No provider coupling — clean provider boundary ✓
- No CLI coupling — CLI imports the package; package does not import CLI ✓
- No stale imports from any closed cleanup track ✓
- Persistence: injected-path JSON, deterministic, `language_report` not-serialized (intentional design) ✓
- Sprint 184 guardrails (9 tests) 9/9 passing ✓
- 1614 passed, 3 skipped | RC2 green | Demo passes ✓

**Changes made:** Documentation closure only. Updated `docs/DecisionJournalCleanupPlan.md` (status CLOSED, Sprint 185 verification table, reopening conditions, Sprint 186 recommendation).

**Next sprint recommendation:** Audit `atlas/watchlist_review/` package.

---

## 2026-07-03: Sprint 184 — Decision Journal Package Audit

Decision: Audit `atlas/decision_journal/` and confirm no cleanup is warranted.

**Rationale:** Sprint 184 performed a full inventory of `atlas/decision_journal/`. The package contains 2 modules (605 lines), 11 active exports, and active CLI callers (`atlas journal create/list/review`) and application callers (`atlas/home/engine.py`). All 11 `__all__` exports are active. No stale imports, no provider coupling, no CLI coupling, no circular dependencies, no dead helpers, no zero-caller exports. JSON persistence is injected-path (not hard-coded in the engine) and fully tested. The `language_report` not-serialized pattern is intentional design (re-derived on load to avoid JSON schema drift).

**Key findings:**
- 2 modules (`__init__.py`, `engine.py`), 605 lines, 11 active exports — all importable ✓
- Active CLI surface: `atlas journal create`, `atlas journal list`, `atlas journal review` ✓
- Active application caller: `atlas/home/engine.py` (journal reminder logic) ✓
- Lateral dependency footprint: `atlas.evidence`, `atlas.language`, `atlas.principles`, `atlas.profile` — all intentional, all runtime-active ✓
- No provider coupling — clean provider boundary ✓
- No stale imports from any closed cleanup track ✓
- `atlas.domains.decision_journal` is a separate thin shim re-exporting `JournalEntry` from `atlas.shared` — distinct from and intentionally separate from `atlas.decision_journal.DecisionJournalEntry` ✓
- 1605 passed, 3 skipped | RC2 green | Demo passes ✓

**Changes made:** Created `docs/DecisionJournalCleanupPlan.md`. Added 9 Sprint 184 guardrail tests in `tests/test_decision_journal_package_sprint184.py`. Updated `docs/LegacyConsolidationPlan.md` and `docs/ArchitectureConsolidation.md`.

**Next sprint recommendation:** Sprint 185 — close decision journal cleanup track (confirm Sprint 184 findings unchanged). After closure, audit `atlas/watchlist_review/`.

---

## 2026-07-03: Sprint 183 — Close Company Analysis Capability Cleanup Track

Decision: Declare `atlas/capabilities/company_analysis/` cleanup track CLOSED.

**Rationale:** After inventory, export review, CLI and pipeline caller review, legacy analysis boundary review, provider boundary review, stale import audit, and Blueprint/capability model review (Sprint 182), the company analysis capability contains only active, intentional code. Sprint 183 confirmed all Sprint 182 findings unchanged. Further cleanup would create churn without architectural benefit.

**Final verified state:**
- 4 modules, 571 lines, 9 active exports — all importable ✓
- Capability does not import `atlas.analysis`; `atlas.analysis` does not import capability ✓
- No provider imports — cleanest provider boundary of any capability ✓
- No CLI imports ✓
- No stale imports from any closed cleanup track ✓
- `CompanyAnalysisProvider` alias remains absent ✓
- 1605 passed, 3 skipped | RC2 green | Demo passes ✓

**Changes made:** Documentation closure only. Updated `docs/CompanyAnalysisCapabilityCleanupPlan.md` (status CLOSED, Sprint 183 verification table, reopening conditions).

**Next sprint recommendation:** Audit `atlas/decision_journal/` package.

---

## 2026-07-03: Sprint 182 — Company Analysis Capability Audit

Decision: Audit `atlas/capabilities/company_analysis/` and confirm no cleanup is warranted.

**Rationale:** Sprint 179 verified the boundary between `atlas/analysis/` and `atlas/capabilities/company_analysis/` from outside. Sprint 182 performed a full internal inventory of the capability itself. The capability has 4 modules (571 lines), 9 exports, and is actively used by the `company-analysis export` CLI command, the daily summary pipeline, the discovery capability, and the watchlist intelligence capability.

**Key findings:**
- All 9 `__all__` exports are active — all either have production callers or are used internally by `engine.py` and verified in tests
- `CompanyAnalysisObservation` and `CompanyAnalysisRisk` have low external reference counts (2 and 1 respectively) but are used extensively inside `engine.py` — not stale
- Zero provider coupling — cleanest provider boundary of any capability audited
- Zero imports from `atlas.analysis`, `atlas.providers`, or `atlas.cli`
- `atlas/analysis/` confirmed not importing capability — bidirectional boundary clean
- 8 private engine helpers are all internal — none dead or test-exposed
- Dependency direction correct: `atlas.shared → atlas.domains → atlas.capabilities`
- No stale imports, no circular dependencies, no upward coupling
- No cleanup warranted

**Changes made:** Audit-only. Created `docs/CompanyAnalysisCapabilityCleanupPlan.md`, added 7 guardrail tests in `tests/test_company_analysis_capability_sprint182.py`.

**Next sprint recommendation:** Close company analysis capability cleanup track (Sprint 183 closure sprint).

---

## 2026-07-03: Sprint 181 — Release Candidate Checkpoint After Company Analysis Residual Cleanup

Decision: Confirm Atlas release-candidate stability after the Sprint 180 company analysis residual cleanup.

**Rationale:** After removing the zero-caller `CompanyAnalysisProvider` alias from the legacy company analysis runtime surface, Atlas remains stable. Active `atlas.analysis` exports remain importable, the Blueprint company analysis capability boundary remains clean, retired CLI paths remain retired, provider boundaries remain unchanged, and release verification remains green.

**Verification results:**
- `CompanyAnalysisProvider` absent from all active runtime code ✓
- All 12 active `atlas.analysis.__all__` exports importable ✓
- `atlas/capabilities/company_analysis/` boundary clean — does not import `atlas/analysis/` ✓
- All 13 deleted modules remain unimportable ✓
- `evidence`, `reason`, `risk` empty groups absent from `atlas --help` ✓
- All 7 retired commands remain non-callable ✓
- All 15 active packages importable ✓
- Provider boundaries unchanged; Yahoo remains opt-in only ✓
- 1598 passed, 3 skipped | RC2 green | Demo passes | Forbidden language check green ✓

**Changes made:** Documentation only. Updated `docs/ReleaseCandidateCheckpoint.md` (Sprint 181 section), `docs/ArchitectureConsolidation.md`, `docs/LegacyConsolidationPlan.md`.

**Next sprint recommendation:** Audit `atlas/capabilities/company_analysis/` cleanup track.

---

## 2026-07-03: Sprint 180 — Remove Stale CompanyAnalysisProvider Alias

Decision: Remove the stale `CompanyAnalysisProvider` alias from `atlas/analysis/company_analysis.py`.

**Rationale:** Sprint 179 confirmed `atlas/company_analysis/` does not exist as a top-level package and audited the actual company analysis surfaces: `atlas/analysis/` and `atlas/capabilities/company_analysis/`. The only actionable cleanup was a non-exported zero-caller `CompanyAnalysisProvider` alias (`from atlas.providers.base import CompanyDataProvider as CompanyAnalysisProvider`) in `atlas/analysis/company_analysis.py`. Removing it eliminates stale migration residue without changing runtime behavior. This is targeted company-analysis residual cleanup found during Sprint 179 — it does not reopen the Sprint 141 `atlas/analysis/` closure.

**Zero-caller audit:** Repo-wide grep confirmed no external production callers, no CLI callers, no active test imports of `CompanyAnalysisProvider` (excluding the Sprint 179 guard that tested it was absent from `__all__`).

**Changes made:**
- Removed alias line from `atlas/analysis/company_analysis.py`
- Updated `tests/test_company_analysis_package_sprint179.py` — replaced `__all__` absence guard with three deletion guardrails: alias not importable, not in `__all__`, not in module namespace
- Updated `docs/CompanyAnalysisCleanupPlan.md` — status CLOSED
- All 12 active `atlas.analysis.__all__` exports preserved
- 1598 tests passed, RC2 green, demo passes
- No runtime behavior changed

**Next sprint recommendation:** Release candidate checkpoint.

---

## 2026-07-03: Sprint 179 — Company Analysis Package Audit

Decision: Audit the legacy company analysis runtime surface (`atlas/analysis/`) and confirm the boundary with `atlas/capabilities/company_analysis/`.

**Rationale:** Sprint 179 was specified as auditing `atlas/company_analysis/`, which does not exist as a standalone package. The company analysis runtime surface is `atlas/analysis/` — the legacy scoring and investment-report layer partially cleaned up in Sprint 141. This audit establishes whether the remaining 5 modules are clean and whether the Sprint 141 closure is verified stable.

**Key findings:**
- `atlas/company_analysis/` does not exist; the legacy surface is `atlas/analysis/` (5 modules, ~655 lines)
- Sprint 141 closure verified: 12 deleted modules remain unimportable
- All 12 `__all__` exports are active with production callers
- `atlas/capabilities/company_analysis/` is fully decoupled from `atlas/analysis/` — capability does not import the legacy layer; boundary is clean
- One stale alias found: `CompanyAnalysisProvider` in `atlas/analysis/company_analysis.py:154` — module-level import of `CompanyDataProvider` aliased to `CompanyAnalysisProvider`, with zero external callers and not in `__all__`
- `ThresholdRecommendationPolicy` generates legacy recommendation language ("Strong Buy"/"Buy"/etc.) — pre-existing, confined to the legacy layer, not emitted by the Blueprint capability
- Provider boundary correct — no direct network access in `atlas/analysis/`; Yahoo remains opt-in only

**Changes made:** Audit-only. Created `docs/CompanyAnalysisCleanupPlan.md`, added 11 guardrail tests in `tests/test_company_analysis_package_sprint179.py`.

**Next sprint recommendation:** Close `atlas/analysis/` cleanup track — remove stale `CompanyAnalysisProvider` alias from `atlas/analysis/company_analysis.py:154`.

---

## 2026-07-03: Sprint 178 — Adapters Package Audit

Decision: Audit `atlas/adapters/` and confirm no cleanup is warranted.

**Rationale:** After auditing capabilities (Sprint 176) and domains (Sprint 177), `atlas/adapters/` was the next audit target — the translation layer bridging external/legacy JSON to Blueprint-aligned types. Full inventory confirmed 5 adapter modules, 756 lines, 7 public symbols.

**Key findings:**
- All 5 adapters are pure JSON-to-type translators: deterministic, no network, no provider imports, no business logic
- All 7 public symbols have active production callers; no zero-caller symbols
- `atlas.analysis.scores.clamp_score` import in `portfolio.py` is correct and active (not stale) — confirmed retained Sprint 140
- Portfolio boundary CLOSED Sprint 148 verified stable: 3 active symbols importable, 6 deleted symbols absent
- No adapter imports `atlas.providers`, `atlas.cli`, or any network library
- No circular dependencies; dependency direction: adapter → domain/capability/shared/active-utilities
- No `__all__` in `__init__.py` is correct — adapters consumed by direct module path
- No cleanup warranted

**Changes made:** Audit-only. Created `docs/AdaptersCleanupPlan.md`, added 14 guardrail tests in `tests/test_adapters_package_sprint178.py`.

**Next sprint recommendation:** Audit `atlas/company_analysis/` package.

---

## 2026-07-03: Sprint 177 — Domains Package Audit

Decision: Audit `atlas/domains/` and confirm no cleanup is warranted.

**Rationale:** After auditing the capabilities layer (Sprint 176), the next audit target was the domain layer — the foundational Blueprint contracts that capabilities depend on. Full inventory confirmed 9 subpackages, ~1,730 lines, 68 total active exports. No stale imports, no provider coupling, no upward dependencies, no circular dependencies. Boundary direction is correct throughout: `atlas.shared → atlas.domains → atlas.capabilities`.

**Key findings:**
- 4 substantive domain subpackages (`decision`, `knowledge`, `portfolio`, `research`) are foundational and widely consumed
- 5 thin/placeholder subpackages (`ai`, `authentication`, `daily_brief`, `decision_journal`, `watchlist`) are correct future-boundary markers
- `atlas.domains.decision.ReasoningEngine` is the active Blueprint-layer class — distinct from deleted `atlas.reasoning.ReasoningEngine`; existing Sprint 163 guardrails confirm this
- `atlas/domains/ai/` re-exports Protocol interfaces from `atlas.ai` — correct future-AI boundary, test-adjacent only, no production callers
- No cleanup warranted

**Changes made:** Audit-only. Created `docs/DomainsCleanupPlan.md`, added 18 guardrail tests in `tests/test_domains_package_sprint177.py`.

**Next sprint recommendation:** Audit `atlas/adapters/` package.

---

## 2026-07-03: Sprint 176 — Capabilities Package Audit

Decision: Audit `atlas/capabilities/` and confirm no cleanup is warranted.

**Rationale:** After 15 closed cleanup tracks and three RC checkpoints, `atlas/capabilities/` was the next highest-leverage audit target. Full inventory confirmed 5 subpackages (4 active + 1 closed Sprint 171), 52 total active exports, no stale imports, no provider coupling, no circular dependencies, no overlap with domain layer beyond correct dependency direction.

**Findings:**
- All capability exports are active and have production callers
- Dependency direction is consistently: `domains/shared → capabilities`; no reverse coupling
- `discovery` is the aggregating capability — correctly imports `CompanyAnalysisReport` and `WatchlistIntelligenceReport`
- `WatchlistInput.from_json_file()` in models is a minor file-I/O note; not a risk
- `atlas/domains/daily_brief/` is a correctly empty placeholder namespace; `atlas/capabilities/daily_brief/` owns the implementation
- `portfolio_intelligence/` subtrack remains closed (Sprint 171); verified stable
- No cleanup warranted

**Changes made:** Audit-only. Created `docs/CapabilitiesCleanupPlan.md`, added 12 guardrail tests in `tests/test_capabilities_package_sprint176.py`.

**Next sprint recommendation:** Audit `atlas/domains/` package.

---

## 2026-07-03: Sprint 175 — RC Checkpoint After 15 Closed Cleanup Tracks

Decision: Treat Atlas as RC2-stable after 15 closed cleanup tracks and three RC checkpoints (Sprint 163, Sprint 172, Sprint 175).

**Rationale:** All 15 cleanup tracks verified closed. All 13 deleted modules confirmed absent. All 10 active packages importable. CLI help surface reflects Sprint 174 change (empty groups absent). Provider boundary unchanged. 1541 tests passed, 3 skipped. RC2 green. Daily brief demo passes.

**Closed-track summary (15 tracks):**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- `atlas/evidence/` cleanup — CLOSED Sprint 150
- `atlas/reasoning/` cleanup — CLOSED Sprint 153
- `atlas/risk/` cleanup — CLOSED Sprint 155
- `atlas/principles/` cleanup — CLOSED Sprint 158
- `atlas/comparison/` cleanup — CLOSED Sprint 160
- `atlas/home/` cleanup — CLOSED Sprint 162
- `atlas/intelligence/` cleanup — CLOSED Sprint 165
- `atlas/conversation/` cleanup — CLOSED Sprint 167
- `atlas/dashboard/` cleanup — CLOSED Sprint 169
- `atlas/capabilities/portfolio_intelligence/` cleanup — CLOSED Sprint 171
- `atlas/cli/` cleanup — CLOSED Sprint 174

**Next sprint recommendation:** Audit `atlas/capabilities/` package (excluding `portfolio_intelligence/`, already closed Sprint 171).

---

## 2026-07-03: Sprint 174 — Remove Empty CLI Groups and Close CLI Cleanup Track

Decision: Remove empty shell CLI app groups and close the CLI cleanup track.

**Rationale:** After the CLI registry audit (Sprint 173), the only actionable cleanup was removing empty `evidence`, `reason`, and `risk` CLI groups from `atlas/cli/main.py`. These groups were residual scaffolding from retired commands (`atlas evidence assess`, `atlas reason analyze`, `atlas risk size`). They exposed no callable commands and only cluttered `atlas --help`. Removing them improves CLI clarity without changing any active or retired command behavior.

**Changes made:** Removed 3 app declarations and 3 `app.add_typer()` registrations (~6 lines total) from `atlas/cli/main.py`. Zero behavioral change — no callable command was removed.

**Verified:**
- `atlas --help` no longer shows `evidence`, `reason`, or `risk` groups ✓
- All active groups remain (intelligence, dashboard, principles, risk-drift, watchlist, daily, portfolio, etc.) ✓
- All 7 retired commands remain not callable ✓
- `_RETIRED_REGISTRY` unchanged — 7 entries, all accurate ✓
- 1536 tests passed, 3 skipped ✓
- RC2 green ✓

**Closed-track summary (15 tracks):**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — CLOSED Sprint 153
- Risk package — CLOSED Sprint 155
- Principles package — CLOSED Sprint 158
- Comparison package — CLOSED Sprint 160
- Home package — CLOSED Sprint 162
- Intelligence package — CLOSED Sprint 165
- Conversation package — CLOSED Sprint 167
- Dashboard package — CLOSED Sprint 169
- Portfolio intelligence capability — CLOSED Sprint 171
- **CLI deprecated command registry — CLOSED Sprint 174**

**Sprint 175 recommended target:** Release candidate checkpoint after 15 closed tracks — pattern matches Sprint 163 (after 10 tracks) and Sprint 172 (after 14 tracks).

---

## 2026-07-03: Sprint 173 — CLI Deprecated Command Registry Audit Checkpoint

Decision: `atlas/cli/` deprecated command registry is clean. One cleanup action is warranted: remove 3 empty shell app groups.

**Rationale:** After audit-first inventory (Sprint 173), the CLI registry is accurate and complete. `_REGISTRY` is correctly empty (all deprecated commands retired Sprint 91). All 7 `_RETIRED_REGISTRY` entries are accurate after 14 cleanup closures — all retirement metadata verified against repository reality. No retired command is accidentally callable. Provider boundary is correct: `_provider_from_name()` in CLI only; default mock; Yahoo opt-in only.

**One cleanup candidate found:** Three sub-app groups are declared and registered in `main.py` but contain zero commands: `evidence_app` (`atlas evidence`), `reason_app` (`atlas reason`), `risk_app` (`atlas risk`). These are residual scaffolding from the retired commands `atlas evidence assess`, `atlas reason analyze`, and `atlas risk size`. They expose empty CLI groups confusing to users. Removing them is a 6-line-per-group change with zero behavioral impact.

**Stale metadata confirmed accurate:** All `removal_criteria` strings verified:
- `atlas evidence assess`: `atlas.evidence` still imported by comparison, decision_journal, watchlist_review ✓
- `atlas risk size`: `RiskAnalysis` still imported by conversation and intelligence ✓
- `atlas portfolio review`: `PortfolioReviewEngine` still instantiated by `atlas/home/engine.py` ✓

**Sprint 174 recommended target:** Remove empty shell CLI app groups (`evidence_app`, `reason_app`, `risk_app`) and close the CLI cleanup track. This closes a 15th cleanup track.

---

## 2026-07-03: Sprint 172 — Release Candidate Checkpoint After 14 Cleanup Closures

Decision: Atlas is release-candidate stable after 14 cleanup track closures.

**Rationale:** After closing analysis, decision, providers, portfolio boundary, evidence, reasoning, risk, principles, comparison, home, intelligence, conversation, dashboard, and portfolio intelligence capability cleanup tracks (Sprints 141–171), Atlas remains stable. Deleted modules remain absent, active modules remain importable, retired CLI paths remain retired, provider boundaries remain unchanged, and release verification remains green.

**Verification results:**
- All 13 deleted modules absent ✓
- All 9 active packages importable ✓
- All 7 retired CLI commands remain retired; `_REGISTRY` empty ✓
- All active CLI commands remain active ✓
- Provider boundaries unchanged across all 6 audited packages ✓
- 1524 tests passed, 3 skipped ✓
- `scripts/verify_release_candidate.sh` — RC2 green ✓
- `scripts/run_daily_brief_demo.sh` — provider-free, passes ✓
- No stale active runtime references found ✓

**Notable stale symbol classifications (all expected):**
- `atlas/domains/decision/engine.py` `ReasoningEngine` — distinct Blueprint-layer class, not the deleted `atlas.reasoning.ReasoningEngine`
- `atlas/providers/yahoo.py` `YahooCompany`, `YahooFinancials`, `YahooMarketData` — active internal types in opt-in Yahoo provider, not stale references
- `atlas/capabilities/portfolio_intelligence/models.py` legacy type doc-comments — migration notes only, not imports

**Sprint 173 recommended target:** Audit `atlas/cli/` deprecated command registry — after 14 cleanup closures and two RC checkpoints, the CLI command surface is the next smallest high-leverage audit target.

---

## 2026-07-03: Sprint 171 — Close Portfolio Intelligence Capability Cleanup Track

Decision: Close the `atlas/capabilities/portfolio_intelligence/` cleanup track. No further cleanup work is warranted.

**Rationale:** After inventory (Sprint 170) and final verification (Sprint 171), the portfolio intelligence capability contains only active, intentional code. `PortfolioIntelligenceCapability.analyze()` is the sole public method, consumed by 5 production packages (decision, intelligence, conversation, dashboard, providers). All 4 exports are active. Dependency surface is minimal — the capability depends only on `atlas.shared.entities` and its own sibling models module. No provider imports. No network calls. No deleted-module imports. No circular dependencies. Further cleanup would create churn without architectural benefit.

**Final verification (Sprint 171):** All 4 exports importable. All 5 production consumer packages confirmed active. Provider boundary confirmed: no concrete provider class imported anywhere in the capability. Zero stale closed-track imports. No Blueprint-aligned successor introduced. No cleanup action warranted.

**Docstring cleanup performed:** Removed stale "Future expansion" note (`themes`, `knowledge_context` fields never added) and completed-migration field-mapping table from `PortfolioFitInput` docstring in `models.py`. Documentation-only change; zero runtime impact.

**Closed-track summary (14 tracks):**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — CLOSED Sprint 153
- Risk package — CLOSED Sprint 155
- Principles package — CLOSED Sprint 158
- Comparison package — CLOSED Sprint 160
- Home package — CLOSED Sprint 162
- Intelligence package — CLOSED Sprint 165
- Conversation package — CLOSED Sprint 167
- Dashboard package — CLOSED Sprint 169
- **Portfolio intelligence capability — CLOSED Sprint 171**

**Sprint 172 recommended target:** Release candidate checkpoint — after closing 14 cleanup tracks, Atlas should run a full RC checkpoint before starting another broad package audit. Pattern matches Sprint 163 (RC after 10 tracks).

---

## 2026-07-03: Sprint 170 — Portfolio Intelligence Capability Audit Checkpoint

Decision: `atlas/capabilities/portfolio_intelligence/` is clean and architecturally exemplary. No cleanup work is warranted.

**Finding — package identity:** `atlas/portfolio_intelligence/` does NOT exist as a top-level package. The legacy `PortfolioIntelligenceEngine` was deleted Sprint 128; `atlas.analysis.portfolio` was deleted Sprint 135. The active Blueprint-aligned surface is `atlas/capabilities/portfolio_intelligence/` (3 modules, 4 exports, 471 lines total).

**Rationale:** After audit-first inventory (Sprint 170), the capability package contains only active, intentional code. `PortfolioIntelligenceCapability.analyze()` is the sole public method, consumed by 5 production packages (decision, intelligence, conversation, dashboard, providers). All 4 exports are active. All 17 private helpers are active. Dependency surface is minimal — the capability depends only on `atlas.shared.entities` (Holding, Portfolio) and its own sibling models module. No provider imports. No network calls. No deleted-module imports. No circular dependencies.

**Notable:** This is the most architecturally sound capability audited so far. The dependency direction is exemplary: providers supply `PortfolioFitInput` → CLI passes to engines → engines pass to capability. The capability knows nothing about providers.

**Stale comment candidate:** `models.py:42–44` contains a "Future expansion" note for `themes` and `knowledge_context` fields that were never added to `PortfolioFitInput`. Docstring-only — no runtime impact. Cleanup candidate for Sprint 171.

**Sprint 171 recommended target:** Close `atlas/capabilities/portfolio_intelligence/` cleanup track — optional docstring cleanup (stale future-expansion note) + documentation track closure.

---

## 2026-07-03: Sprint 169 — Close Dashboard Cleanup Track

Decision: Close the `atlas/dashboard/` cleanup track. No cleanup work is warranted.

**Rationale:** After inventory (Sprint 168) and final verification (Sprint 169), the dashboard package contains only active, intentional code. `DashboardEngine.build()` is the sole public method, active at 1 production call site (CLI `atlas dashboard show`). All 6 exports are active. All 17 private helpers are active. Dashboard has the cleanest provider boundary of any audited package — it imports no concrete provider class at all. `CompanyDataProvider` is used only as a type annotation in `DashboardInput.provider`. Provider selection lives entirely at the CLI layer. No stale imports. No Blueprint-aligned successor. Further cleanup would create churn without architectural benefit.

**Final verification (Sprint 169):** All 6 exports importable. `atlas dashboard show` CLI entrypoint confirmed active. Provider boundary confirmed cleanest of any audited package. Zero stale closed-track imports. No new Blueprint successor. No cleanup action warranted.

**Closed-track summary (13 tracks):**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — CLOSED Sprint 153
- Risk package — CLOSED Sprint 155
- Principles package — CLOSED Sprint 158
- Comparison package — CLOSED Sprint 160
- Home package — CLOSED Sprint 162
- Intelligence package — CLOSED Sprint 165
- Conversation package — CLOSED Sprint 167
- **Dashboard package — CLOSED Sprint 169**

**Sprint 170 recommended target:** Audit `atlas/portfolio_intelligence/` package — a major active domain-adjacent runtime surface, natural next step after dashboard is closed.

---

## 2026-07-03: Sprint 168 — Dashboard Package Audit Checkpoint

Decision: `atlas/dashboard/` package is clean. No cleanup work is warranted.

**Rationale:** After audit-first inventory (Sprint 168), the dashboard package contains only active, intentional code. All 6 exports are active. `DashboardEngine.build()` is the sole public method, active at 1 production call site (CLI `atlas dashboard show`). All 17 private helpers are active. No zero-caller symbols. No stale exports. No closed-track import residue. No Blueprint-aligned successor exists. Dashboard has the cleanest provider boundary of any audited package — it imports only `CompanyDataProvider` as a type annotation and never imports any concrete provider class. Provider selection lives entirely at the CLI layer. Dashboard does not import `atlas.intelligence` or `atlas.conversation` — it orchestrates independently at the application layer.

**Notable:** Dashboard calls `_dashboard_text_without_principles()` twice — once before `PrinciplesEngine.check()` (for principles pre-check on draft text) and once via `render_dashboard()` at CLI time. This is an intentional design pattern.

**Sprint 169 recommended target:** Close the dashboard cleanup track — documentation-only sprint confirming audit findings. Pattern matches Sprint 150, 155, 158, 160, 162, 165, and 167.

---

## 2026-07-03: Sprint 167 — Close Conversation Cleanup Track

Decision: Close the `atlas/conversation/` cleanup track. No cleanup work is warranted.

**Rationale:** After inventory (Sprint 166) and final verification (Sprint 167), the conversation package contains only active, intentional code. `ConversationEngine.answer()` is the sole public method, active at 1 production call site (CLI `atlas ask`). All 6 exports are active. All 16 private helpers are active. `IntelligenceEngine` dependency is intentional — consumed by `_answer_company_analysis` and `_answer_general_guidance` intent branches. `RiskAnalysis` dependency is intentional, optional, and shallow. No stale imports. No Blueprint successor. Further cleanup would create churn without architectural benefit.

**Final verification (Sprint 167):** All 6 exports importable. `atlas ask` CLI entrypoint confirmed active. Intelligence and risk dependencies confirmed intentional. Zero stale closed-track imports. No new Blueprint successor. Provider boundary unchanged. No cleanup action warranted.

**Closed-track summary:**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — CLOSED Sprint 153
- Risk package — CLOSED Sprint 155
- Principles package — CLOSED Sprint 158
- Comparison package — CLOSED Sprint 160
- Home package — CLOSED Sprint 162
- Intelligence package — CLOSED Sprint 165
- **Conversation package — CLOSED Sprint 167**

**Sprint 168 recommended target:** Audit `atlas/dashboard/` package — another active runtime/application-facing surface, natural next step after conversation is closed.

---

## 2026-07-03: Sprint 166 — Conversation Package Audit Checkpoint

Decision: `atlas/conversation/` package is clean. No cleanup work is warranted.

**Rationale:** After audit-first inventory (Sprint 166), the conversation package contains only active, intentional code. All 6 exports are active and consumed by CLI (`atlas ask`) and `atlas/principles/engine.py` (TYPE_CHECKING only). `ConversationEngine.answer()` is the sole public method, active at 1 production call site (CLI). All 16 private helpers are active. No zero-caller symbols. No stale exports. No closed-track import residue. No Blueprint-aligned successor exists. Provider boundary is clean and opt-in — `MockCompanyAnalysisProvider` is the default fallback; `YahooFinanceProvider` never imported. Intelligence dependency (`IntelligenceEngine`) is intentional and consumed by 2 of 8 intent branches. `RiskAnalysis` dependency is intentional, optional, and shallow.

**Sprint 167 recommended target:** Close the conversation cleanup track — documentation-only sprint confirming audit findings. Pattern matches Sprint 150, 155, 158, 160, 162, and 165.

---

## 2026-07-03: Sprint 165 — Close Intelligence Cleanup Track

Decision: Close the `atlas/intelligence/` cleanup track. No cleanup work is warranted.

**Rationale:** After inventory (Sprint 164) and final verification (Sprint 165), the intelligence package contains only active, intentional code. `IntelligenceEngine.analyze()` is the sole public method, active at 3 production call paths (CLI×2, conversation). All 5 exports are active. All 13 private helpers are active. `RiskAnalysis` dependency is intentional, optional, and shallow. No stale imports. No Blueprint successor. Further cleanup would create churn without architectural benefit.

**Final verification (Sprint 165):** All 5 exports importable. `atlas intelligence analyze` and `atlas daily summary` CLI paths confirmed active. Conversation and suitability integrations confirmed intentional. Zero stale closed-track imports. No new Blueprint successor. No provider boundary violation. No cleanup action warranted.

**Closed-track summary:**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — CLOSED Sprint 153
- Risk package — CLOSED Sprint 155
- Principles package — CLOSED Sprint 158
- Comparison package — CLOSED Sprint 160
- Home package — CLOSED Sprint 162
- **Intelligence package — CLOSED Sprint 165**

**Sprint 166 recommended target:** Audit `atlas/conversation/` package — an active runtime orchestration surface that depends on intelligence (now closed) and is a natural next step in the cleanup sequence.

---

## 2026-07-03: Sprint 164 — Intelligence Package Audit Checkpoint

Decision: `atlas/intelligence/` package is clean. No cleanup work is warranted.

**Rationale:** After audit-first inventory (Sprint 164), the intelligence package contains only active, intentional code. All 5 exports are active and consumed by CLI (2 commands), `atlas/conversation/engine.py`, and `atlas/suitability/engine.py`. `IntelligenceEngine.analyze()` is the sole public method and has 3 production call sites. All 13 private helpers are internal and active. No zero-caller symbols exist. No stale exports. No closed-track import residue. No Blueprint-aligned successor exists. Provider boundary is clean and opt-in. The `RiskAnalysis` dependency is intentional, optional at call time, and shallow (4 fields read).

**One correction made:** `atlas/cli/deprecations.py` `removal_criteria` for `atlas risk size` previously mentioned `atlas/reasoning engines` as a `RiskAnalysis` caller (stale since Sprint 153). Corrected to `atlas/conversation and atlas/intelligence engines`. Metadata-only, no runtime impact.

**Sprint 165 recommended target:** Close the intelligence cleanup track — documentation-only sprint confirming audit findings. Pattern matches Sprint 150, 155, 158, 160, and 162.

---

## 2026-07-03: Sprint 163 — Release Candidate Checkpoint After Cleanup Closures

Decision: Sprint 163 confirms Atlas release-candidate stability after 10 cleanup tracks were closed.

**Rationale:** After closing analysis, decision, providers, portfolio boundary, evidence, reasoning, risk, principles, comparison, and home cleanup tracks, Atlas remains stable. Deleted modules remain absent, active modules remain importable, retired CLI paths remain retired, provider boundaries remain unchanged, and release verification remains green.

**Verification summary:**
- Deleted modules: `atlas/reasoning/`, `atlas/analysis/portfolio.py`, `atlas/analysis/growth.py`, `atlas/analysis/macro.py`, `atlas/analysis/moat.py`, `atlas/analysis/quality.py`, `atlas/analysis/sentiment.py`, `atlas/analysis/technicals.py`, `atlas/analysis/valuation.py` — all confirmed absent ✓
- Retired symbols (`ReasoningEngine` from `atlas.reasoning`, `PortfolioIntelligenceEngine`, `check_reasoning_report`, `check_intelligence_report`, `check_suitability_assessment`, `PortfolioAnalysis`, `PortfolioSignal`, `render_comparison_result`, etc.) — all hits are expected guardrail tests, docs/comments, or distinct Blueprint-layer classes (e.g. `atlas/domains/decision/` defines its own `ReasoningEngine`, unrelated to deleted `atlas.reasoning`) ✓
- Active packages (`atlas.evidence`, `atlas.risk`, `atlas.principles`, `atlas.comparison`, `atlas.home`) — all importable, all exports intact ✓
- Retired CLI commands (`atlas reason analyze`, `atlas risk size`, `atlas evidence assess`, `atlas portfolio analyze`, `atlas portfolio review`, `atlas watchlist analyze`, `atlas daily brief`) — all in `_RETIRED_REGISTRY`, none registered in `_REGISTRY`, none callable ✓
- Active CLI commands (`atlas home`, `atlas compare`, `atlas daily summary`, `atlas intelligence analyze`, etc.) — all registered and active ✓
- Provider boundaries — `atlas/comparison/` and `atlas/home/` both use `MockCompanyAnalysisProvider` as default; `YahooFinanceProvider` remains CLI opt-in only via `--provider yahoo`; no new provider imports introduced ✓
- Demo: provider-free, deterministic ✓
- RC2: green ✓
- Tests: 1460 passed, 3 skipped ✓

**Stale reference noted (non-blocking):** `atlas/cli/deprecations.py` `removal_criteria` for `atlas risk size` still mentions `atlas/reasoning engines` as a `RiskAnalysis` caller. `atlas/reasoning/` was deleted Sprint 153. The actual current callers are `atlas/intelligence/engine.py` and `atlas/conversation/engine.py`. This is a retired command record (never executed), not a stale active import. No runtime impact. Can be corrected in Sprint 164 during `atlas/intelligence/` audit if desired.

**Sprint 164 recommended target:** Audit `atlas/intelligence/` package. `atlas/intelligence/` is a larger runtime surface and should be audited now that the cleanup closure sequence has been release-verified.

---

## 2026-07-03: Sprint 162 — Close Home Cleanup Track

Decision: Close the `atlas/home/` cleanup track. No cleanup work is warranted.

**Rationale:** After inventory (Sprint 161) and final verification (Sprint 162), the home package contains only active, intentional code. `AtlasHomeEngine` is used by the active `atlas home` CLI command. Provider coupling is clean: `MockCompanyAnalysisProvider` is the default (deterministic, local); `YahooFinanceProvider` is CLI opt-in only and never imported by `atlas/home/` directly. No Blueprint successor exists. Further cleanup would create churn without architectural benefit.

**Final verification (Sprint 162):** All 7 exports importable. CLI caller confirmed active. Zero stale closed-track imports. No new Blueprint successor. No provider boundary violation.

**Closed-track summary:**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — CLOSED Sprint 153
- Risk package — CLOSED Sprint 155
- Principles package — CLOSED Sprint 158
- Comparison package — CLOSED Sprint 160
- **Home package — CLOSED Sprint 162**

**Sprint 163 recommended target:** Audit `atlas/cli/` deprecated command registry — verify each removal criterion is still accurate, check for stale references to now-deleted modules, confirm no deprecated commands have been reintroduced.

---

## 2026-07-03: Sprint 161 — Home Package Audit Checkpoint

Decision: Audit `atlas/home/` as a Group B provider-coupled module. Audit-only sprint. No runtime changes.

**Findings:**
- 2 modules: `__init__.py` (19 lines), `engine.py` (611 lines). 7 exports.
- `AtlasHomeEngine` is active: 1 production caller (CLI `atlas home`), 15 tests. Single `.build()` public method. No zero-caller methods.
- Provider coupling is intentional and clean: `CompanyDataProvider` as type annotation; `MockCompanyAnalysisProvider` as default (deterministic, local). `YahooFinanceProvider` only reachable via `--provider yahoo` CLI flag — never imported by `atlas/home/` itself. Pattern identical to `atlas/comparison/`.
- All 7 exports are active or intentional sub-types. `AtlasHomePriority`, `AtlasHomeMonitoring`, `AtlasHomeSummary` have zero direct external production callers but are correct sub-types of `AtlasHomeOutput`.
- Zero stale closed-track imports. Zero dead code. Zero Blueprint pressure.
- `atlas/home/` **consumes** `WatchlistInput` from `atlas/capabilities/watchlist_intelligence/` — correct direction.
- No `atlas/domains/home/` or `atlas/capabilities/home/` exists. No Blueprint successor.
- `atlas/capabilities/daily_brief/` is conceptually adjacent but not a successor — different scope (daily briefing vs. personalized investor dashboard).

**Sprint 162 recommended target:** Close the home cleanup track — documentation-only sprint confirming no cleanup is warranted. See `docs/HomeCleanupPlan.md`.

---

## 2026-07-03: Sprint 160 — Close Comparison Cleanup Track

Decision: Close the `atlas/comparison/` cleanup track. No cleanup work is warranted.

**Rationale:** After inventory (Sprint 159) and final verification (Sprint 160), the comparison package contains only active, intentional code. `InvestmentComparisonEngine` is used by the active `atlas compare` CLI command. Provider coupling is clean: `MockCompanyAnalysisProvider` is the default (deterministic, local); `YahooFinanceProvider` is CLI opt-in only and never imported by `atlas/comparison/` directly. No Blueprint successor exists. Further cleanup would create churn without architectural benefit.

**Final verification (Sprint 160):** All 9 exports importable. CLI caller confirmed active. Zero stale closed-track imports. No new Blueprint successor. No provider boundary violation.

**Closed-track summary:**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — CLOSED Sprint 153
- Risk package — CLOSED Sprint 155
- Principles package — CLOSED Sprint 158
- **Comparison package — CLOSED Sprint 160**

**Sprint 161 recommended target:** Audit `atlas/home/` — Group B provider-coupled module. Inventory modules, map callers, verify provider boundary, check Blueprint overlap, classify cleanup candidates.

---

## 2026-07-03: Sprint 159 — Comparison Package Audit Checkpoint

Decision: Audit `atlas/comparison/` as a provider-coupled module. Audit-only sprint. No runtime changes.

**Findings:**
- 2 modules: `__init__.py` (23 lines), `engine.py` (1009 lines). 9 exports.
- `InvestmentComparisonEngine` is active: 1 production caller (CLI `atlas compare`), 1 test file. Clean `.compare()` public API; no zero-caller methods.
- Provider coupling is intentional and clean: `CompanyDataProvider` as type annotation; `MockCompanyAnalysisProvider` as default (deterministic, local). `YahooFinanceProvider` only reachable via `--provider yahoo` CLI flag — never imported by `atlas/comparison/` itself.
- All 9 exports are active or intentional sub-types (`InvestmentComparisonObservation`, `InvestmentComparisonSection` have zero direct external callers but are correct sub-types of the active report).
- Zero stale closed-track imports. Zero dead code. Zero Blueprint pressure.
- `atlas/decision/comparison.py` (130 lines) is a completely separate module — score-ranked ticker comparison for the decision flow. No overlap with `InvestmentComparisonEngine`.
- No `atlas/domains/comparison/` or `atlas/capabilities/comparison/` exists. No Blueprint successor.

**Sprint 160 recommended target:** Close the comparison cleanup track — documentation-only sprint confirming no cleanup is warranted. See `docs/ComparisonCleanupPlan.md`.

---

## 2026-07-03: Sprint 158 — Close Principles Cleanup Track

Decision: Close the `atlas/principles/` cleanup track. No further cleanup work is warranted.

**Rationale:** After audit (Sprint 156) and removal of two zero-caller convenience functions (Sprint 157), Sprint 158 confirmed the principles package contains only active, intentional code. `check_reasoning_report` was removed Sprint 152. `check_intelligence_report` and `check_suitability_assessment` were removed Sprint 157 after `atlas/reasoning/` was deleted. The remaining 9 exports are all active or well-tested. Further cleanup would create churn without architectural benefit.

**Final verification (Sprint 158):** All 9 exports importable. 5 known callers confirmed. CLI active. Zero removed-check references in active code. Zero provider imports. Zero stale closed-track imports. No Blueprint successor introduced.

**Closed-track summary:**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — CLOSED Sprint 153
- Risk package — CLOSED Sprint 155
- **Principles package — CLOSED Sprint 158**

**Sprint 159 recommended target:** Audit `atlas/comparison/` — provider-coupled module with known Blueprint overlap (`InvestmentComparisonEngine`). Audit-first: inventory modules, map callers, verify provider boundary, check Blueprint overlap, classify cleanup candidates.

---

## 2026-07-03: Sprint 157 — Remove Dormant Principles Report Checks

Decision: Remove `check_intelligence_report` and `check_suitability_assessment` from `atlas/principles/engine.py` and `atlas/principles/__init__.py`.

**Rationale:** Sprint 156 audit identified both functions as zero-caller (no production or test callers). Each carried a lazy runtime import and TYPE_CHECKING parameter annotation — identical pattern to `check_reasoning_report` removed in Sprint 152. Removal reduces principles public API from 11 to 9 exports with no production behavior changes.

**Changes:** Deleted 2 functions, 2 lazy imports (`render_intelligence_report`, `render_suitability_assessment`), 2 TYPE_CHECKING import names (`IntelligenceReport`, `SuitabilityAssessment`). Updated `__init__.py` imports and `__all__`. Updated guardrail tests. Updated docs.

**Active API preserved:** `PrinciplesEngine`, `PrinciplesCheck`, `render_principles_check`, `check_conversation_response`, `check_text_against_principles`, and all 4 type-system symbols remain unchanged. All 5 production callers unaffected.

**Closed-track summary:**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — CLOSED Sprint 153
- Risk package — CLOSED Sprint 155
- **Principles package — CLOSED Sprint 157**

**Sprint 158 recommended target:** Close principles cleanup track formally (documentation-only sprint confirming stable post-Sprint-157 state). No code changes expected.

---

## 2026-07-02: Sprint 156 — Principles Package Audit Checkpoint

Decision: Audit `atlas/principles/` as a Group C self-contained module. Audit-only sprint. No runtime changes.

**Findings:**
- 2 modules: `__init__.py` (27 lines), `engine.py` (324 lines).
- 11 exports. Core engine active: `PrinciplesEngine` and `PrinciplesCheck` used by 5 production engines (comparison, dashboard, decision_journal, portfolio_review, watchlist_review) + CLI.
- `render_principles_check` used by active `atlas principles check` CLI command.
- Sprint 152 removal of `check_reasoning_report` verified clean — no `atlas.reasoning` references remain.
- **Two zero-caller convenience functions identified:** `check_intelligence_report` and `check_suitability_assessment` — zero production callers, zero test callers. Each contains a lazy import and a TYPE_CHECKING annotation parameter type; identical pattern to `check_reasoning_report` removed in Sprint 152.
- Boundary clean: zero provider imports, zero upward dependencies at module load time.
- No Blueprint-aligned successor; no overlap with `atlas/domains/` or `atlas/capabilities/`.
- No stale closed-track imports.

**Sprint 157 recommended target:** Remove `check_intelligence_report` and `check_suitability_assessment` — two zero-caller convenience functions — following the Sprint 152 pattern. Reduces principles API from 11 to 9 exports. See `docs/PrinciplesCleanupPlan.md`.

**Closed-track summary:**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — CLOSED Sprint 153
- Risk package — CLOSED Sprint 155
- **Principles package — ACTIVE (Sprint 157 cleanup planned)**

---

## 2026-07-02: Sprint 155 — Close Risk Cleanup Track

Decision: Close the `atlas/risk/` cleanup track. No cleanup work is warranted.

**Rationale:** After inventory (Sprint 154), caller verification, stale import audit, and Blueprint overlap review, the risk package contains only active, intentional code. `RiskAnalysis` is still used by 2 production engines (`conversation`, `intelligence`). `RiskEngine` has zero production callers but shares a file with the active type — deletion requires file surgery with no Blueprint migration target. Further cleanup would create churn without architectural benefit.

**Final verification (Sprint 155):** All 8 exports importable. 2 known callers confirmed. Zero provider imports. Zero stale closed-track imports. No Blueprint successor introduced.

**Closed-track summary:**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — CLOSED Sprint 153
- Risk package — **CLOSED Sprint 155**

**Sprint 156 recommended target:** Audit Group C self-contained module `atlas/principles/` — `check_reasoning_report()` was removed Sprint 152, reducing the principles API; remaining exports and callers should be inventoried and confirmed stable.

---

## 2026-07-02: Sprint 154 — Risk Package Audit Checkpoint

Decision: Audit `atlas/risk/` as a Group C self-contained module. Audit-only sprint. No runtime changes.

**Findings:**
- 2 modules: `__init__.py` (21 lines), `engine.py` (448 lines).
- 8 exports in `__all__`: all reachable, but only `RiskAnalysis` has active production callers.
- **`RiskAnalysis` is actively used by 2 production engines:**
  - `atlas/conversation/engine.py` — optional context field in `ConversationInput`
  - `atlas/intelligence/engine.py` — optional context in `IntelligenceInput`/`IntelligenceReport`; accesses `.position_sizing.*` and `.deployment_plan.*` fields
- `RiskEngine` has zero production instantiation points — `atlas risk size` was retired Sprint 88.
- `RiskEngine` and `RiskAnalysis` share the same file. Deleting `RiskEngine` requires separating `RiskAnalysis` to a new file (surgery). No Blueprint migration target exists. Surgery risk outweighs value.
- `render_risk_analysis` is test-only (zero production callers).
- Self-contained boundary: imports only `atlas.analysis.scores.clamp_score` (utility, still active) and `atlas.market.MarketRegime` (expected Group B dependency). No provider, CLI, conversation, or intelligence imports.
- Zero stale closed-track imports (no reasoning, no deleted analysis modules).
- No Blueprint-aligned successor: no `atlas/domains/risk/` or `atlas/capabilities/risk/` exists.
- No dead code, no stale migration residue, no consolidation candidates.
- Full findings in `docs/RiskCleanupPlan.md`.

**Sprint 155 recommendation:** Close risk cleanup track (documentation-only). No cleanup work warranted. `RiskAnalysis` must remain; `RiskEngine` cannot be removed without risky surgery; no Blueprint successor.

---

## 2026-07-02: Sprint 153 — Delete atlas/reasoning/ Package

Decision: Delete `atlas/reasoning/` package entirely (engine.py + __init__.py, 594 lines).

**Rationale:** Sprint 152 removed `check_reasoning_report()` from `atlas/principles/engine.py`, leaving zero production-code dependencies on `atlas.reasoning`. Sprint 153 completes the two-sprint sequence by deleting the dormant package. `atlas reason analyze` was retired Sprint 87; no runtime behavior changes.

**Changes made:**
- `atlas/reasoning/` directory deleted (engine.py, __init__.py, __pycache__/).
- `atlas/cli/deprecations.py` — updated `atlas reason analyze` removal_criteria to confirm deletion done.
- `tests/test_reasoning_engine.py` — rewritten as Sprint 153 deletion guards; engine behavior tests removed; CLI retirement and migration guardrails retained.
- `tests/test_reason_analyze_deprecation.py` — `test_reasoning_engine_module_remains_on_disk` replaced with `test_reasoning_package_deleted` (asserts ModuleNotFoundError).
- `tests/test_reasoning_package_sprint151.py` — removed all `atlas.reasoning` import tests; added Sprint 153 deletion guard; Sprint 152 and closed-track guardrails retained.
- `tests/test_risk_size_deprecation.py` — removed `atlas/reasoning/engine.py` from `RISK_ANALYSIS_CALLERS` tuple.

**Closed-track summary:**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — **CLOSED Sprint 153**

---

## 2026-07-02: Sprint 152 — Remove Dormant Principles Reasoning Report Check

Decision: Remove `check_reasoning_report()` from `atlas/principles/engine.py`. This was a zero-caller function whose sole purpose was to call `render_reasoning_report()` from `atlas.reasoning` via a lazy import. Removing it eliminates the only remaining production-code dependency on `atlas.reasoning`.

**Changes made:**
- `atlas/principles/engine.py` — deleted `check_reasoning_report()` (4 lines), removed TYPE_CHECKING import of `ReasoningReport`, removed lazy import of `render_reasoning_report`.
- `atlas/principles/__init__.py` — removed `check_reasoning_report` import and `__all__` entry (11 active exports remain).
- `atlas/cli/deprecations.py` — updated `atlas reason analyze` removal_criteria to reflect Sprint 152 blocker resolved.
- `tests/test_reason_analyze_deprecation.py` — replaced `test_principles_engine_lazy_import_is_still_present` with `test_principles_engine_no_longer_references_atlas_reasoning` and `test_principles_engine_does_not_export_check_reasoning_report`.
- `tests/test_reasoning_package_sprint151.py` — replaced Sprint 151 lazy-import presence assertions with Sprint 152 removal assertions.

**Result:** `atlas/principles/engine.py` has zero references to `atlas.reasoning`. No production code references `atlas.reasoning` at runtime. `atlas/reasoning/` package remains on disk — deletion deferred to Sprint 153.

**Sprint 153 recommendation:** Delete `atlas/reasoning/` package entirely (engine.py + __init__.py, 594 lines of dormant code).

---

## 2026-07-02: Sprint 151 — Reasoning Package Audit Checkpoint

Decision: Audit `atlas/reasoning/` as a Group C self-contained module. Audit-only sprint. No runtime changes.

**Findings:**
- 2 modules: `__init__.py` (19 lines), `engine.py` (575 lines).
- 7 exports in `__all__`: all reachable from `__init__.py`, but zero have active runtime production callers.
- CLI command `atlas reason analyze` was retired Sprint 87. Zero production code instantiates `ReasoningEngine`.
- Sole production-code reference: `atlas/principles/engine.py` holds (a) a TYPE_CHECKING-only import of `ReasoningReport` (line 9) and (b) a lazy runtime import of `render_reasoning_report` inside `check_reasoning_report()` (line 147).
- `check_reasoning_report()` has zero external callers — confirmed Sprint 87, confirmed Sprint 151.
- `check_reasoning_report()` is exported in `atlas/principles/__init__.py` but unreachable in any production path.
- The lazy import was introduced to avoid a transitive circular import chain (`atlas.reasoning` imports `atlas.analysis.engine`, `atlas.capabilities.portfolio_intelligence`, `atlas.risk`, `atlas.economics`, `atlas.market`, `atlas.monitoring`, `atlas.themes`).
- Self-contained boundary: zero imports from `atlas/providers/`, `atlas/cli/`, `atlas/dashboard/`, `atlas/conversation/`, `atlas/intelligence/`, `atlas/domains/`, or deleted analysis modules.
- Blueprint overlap: `atlas/domains/decision/engine.py` has its own `ReasoningEngine` and `Evidence` (completely different purpose — Blueprint decision reasoning). No migration warranted. No conflict.
- Zero stale closed-track imports.
- No dead private helpers; all are internal to the dormant engine.
- Full findings in `docs/ReasoningCleanupPlan.md`.

**Sprint 152 recommendation:** Remove `check_reasoning_report()` from `atlas/principles/engine.py` (zero callers, only production dependency on `atlas.reasoning`). This unblocks Sprint 153: full deletion of `atlas/reasoning/` package (594 lines of dormant code).

---

## 2026-07-02: Sprint 150 — Close Evidence Cleanup Track

Decision: Close the `atlas/evidence/` cleanup track. No cleanup work is warranted.

**Rationale:** After inventory (Sprint 149), caller verification, stale import audit, Blueprint overlap review, and Sprint 150 final verification, the evidence package contains only active, intentional code. It is self-contained, imports only `atlas.language`, is actively used by 3 production engines (`comparison`, `decision_journal`, `watchlist_review`), and has no dead code, no stale migration residue, and no Blueprint-aligned successor. Further cleanup would create churn without architectural benefit.

**Final verification (Sprint 150):** All 9 exports importable. 3 known callers confirmed. Zero upward dependencies. Zero stale imports. No successor introduced.

**Closed-track summary:**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — **CLOSED Sprint 150**

**Sprint 151 recommended target:** Audit Group C self-contained module `atlas/reasoning/` — known lazy import tech debt (`atlas/principles/` lazy import of `render_reasoning_report`, documented Sprint 87). Smallest safe Group C audit-first target.

---

## 2026-07-02: Sprint 149 — Evidence Package Audit Checkpoint

Decision: Audit `atlas/evidence/` as a Group C self-contained module. Audit-only sprint. No runtime changes.

**Findings:**
- 2 modules: `__init__.py` (23 lines), `engine.py` (540 lines).
- 9 exports in `__all__`: all intentional. No stale exports.
- 3 production engine callers confirmed (exactly as expected): `atlas/comparison/engine.py`, `atlas/decision_journal/engine.py`, `atlas/watchlist_review/engine.py`. No additional callers found.
- All 3 callers inject `EvidenceQualityEngine` and consume `EvidenceAssessment` fields for scoring and routing.
- Self-contained boundary: imports only from `atlas.language` (Group D infrastructure). No provider, CLI, dashboard, conversation, intelligence, or decision imports.
- Zero stale closed-track imports.
- `render_evidence_assessment` is exported but has zero production callers — test-only usage in `test_evidence_engine.py`. Not a critical cleanup target.
- `atlas/domains/decision/` has its own `Evidence`/`EvidenceStrength`/`EvidenceCategory` types — naming overlap only. Different purpose (structured evidence items with category taxonomy) vs. `atlas/evidence/` (source quality assessment engine). No migration warranted.
- No Blueprint-aligned successor exists.
- No dead helpers, no stale migration residue, no duplicated logic.

**Sprint 150 recommendation:** Close the evidence cleanup track — no cleanup work is warranted. Package is stable and active.

---

## 2026-07-02: Sprint 148 — Close Portfolio Boundary Cleanup Track

Decision: Remove the stale `PortfolioFitInput` import from `atlas/adapters/portfolio.py` and close the portfolio boundary cleanup track.

**Rationale:** After deleting `atlas.analysis.portfolio` (Sprint 135), removing the identity adapter `portfolio_fit_input_from_profile` (Sprint 137), auditing all remaining callers (Sprint 147), and now removing the final stale `PortfolioFitInput` import, the adapter boundary is intentional and stable. `Portfolio` and `PortfolioPosition` are the correct permanent home for legacy CLI JSON-loading boundary types. No Blueprint-aligned JSON-loading type exists as a replacement, and the adapter has no upward dependencies. No further cleanup is warranted.

**Change:** One import line removed from `atlas/adapters/portfolio.py`. Zero behavior change.

**Closed-track summary:**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — **CLOSED Sprint 148**

**Sprint 149 recommended target:** Audit Group C self-contained module `atlas/evidence/` — self-contained, no provider dependency, 3 active engine callers, no Blueprint successor yet. Smallest safe audit-first step.

---

## 2026-07-02: Sprint 147 — Portfolio Boundary Caller Audit

Decision: Audit all remaining callers of `Portfolio`, `PortfolioPosition`, and `legacy_portfolio_to_domain_portfolio` from `atlas/adapters/portfolio.py`. No runtime changes.

**Findings:**
- Zero stale `atlas.analysis.portfolio` imports in production code — deletion from Sprint 135 is complete and stable.
- 9 CLI `Portfolio.from_json_file` call sites across 9 commands: `ask`, `home`, `dashboard show`, `daily summary`, `portfolio summary`, `intelligence analyze`, `suitability analyze`, `risk-drift analyze`, `monitor`. All correct and permanent — these are the JSON-loading boundary.
- 8 engine files use `Portfolio` as a TYPE_CHECKING-only type annotation: `conversation`, `decision_context`, `dashboard`, `home`, `intelligence`, `monitoring`, `risk_drift`, `suitability`. All correct.
- 6 runtime callers of `legacy_portfolio_to_domain_portfolio`: CLI (×2), `conversation`, `dashboard`, `decision_engine`, `intelligence`, `portfolio_review`. All correct.
- `atlas/portfolio_review/engine.py` is the only engine that imports `Portfolio as LegacyPortfolio` at module runtime (not behind TYPE_CHECKING) — intentional: it constructs the review input from a legacy Portfolio.
- Adapter boundary is clean: no upward dependencies, no provider imports, no CLI imports.
- **One stale import in adapter:** `from atlas.capabilities.portfolio_intelligence import PortfolioFitInput` at line 33 — imported but unused. Left over from Sprint 133.
- No Blueprint-aligned JSON-loading type exists. `atlas.adapters.portfolio.Portfolio` is the correct permanent home.

**Sprint 148 target:** Remove stale `PortfolioFitInput` import from adapter, add boundary guardrail, close portfolio boundary track.

---

## 2026-07-02: Sprint 146 — Remove Stale Yahoo Provider Re-exports

Decision: Remove `YahooCompany`, `YahooFinancials`, `YahooMarketData` from `atlas/providers/__init__.py`.

**Rationale:** Zero external callers confirmed by repo-wide grep (Sprint 145 audit). These types are implementation details of `YahooFinanceProvider` — internal data transfer objects used within `yahoo.py` to fetch and parse raw Yahoo Finance API responses before assembling `CompanyAnalysis` and `PortfolioFitInput`. Exposing them in `__init__.py` incorrectly suggested they were part of the provider contract. Removing them from the public surface tightens the API to reflect actual usage without changing any runtime behavior.

**Changes:**
- `atlas/providers/__init__.py`: 3 imports and 3 `__all__` entries removed. File reduced from 19 to 14 lines. `__all__` reduced from 7 to 4 exports.
- `atlas/providers/yahoo.py`: unchanged. Types retained for internal use.
- `tests/test_provider_package_sprint145.py`: `test_sprint145_atlas_providers_all_exports` updated to expect only 4 active exports. 3 Sprint 146 guardrail tests added.
- 4 docs updated.

**Provider boundary audit track:** CLOSED. All identified cleanup complete.

**Recommended Sprint 147 target:** No remaining provider cleanup. Pivot to next technical debt area — `atlas/analysis/portfolio.py` caller migration audit or Group C self-contained module Blueprint wrappers.

---

## 2026-07-02: Sprint 145 — Provider Boundary Audit

Decision: Begin `atlas/providers/` boundary audit. Audit-only sprint. No runtime changes.

**Findings:**
- 4 modules, 539 lines total.
- `CompanyDataProvider` protocol: 2 methods. `get_company_analysis` has 7 production call sites; `get_portfolio_profile` has 4. Both return correct types (`CompanyAnalysis`, `PortfolioFitInput`). `get_portfolio_profile` returning `PortfolioFitInput` confirmed (Sprint 133).
- `MockCompanyAnalysisProvider`: clean, 5 supported tickers for analysis, 4 for portfolio profile (AMD intentionally excluded from portfolio profiles).
- `YahooFinanceProvider`: correct contract implementation. Yahoo-specific sub-methods (`get_company`, `get_financials`, `get_market_data`) are internal-only; no production code outside `providers/` calls them.
- Zero stale production imports. No boundary violations (providers do not import from decision/intelligence/CLI/dashboard).
- Blueprint alignment: both contract methods return stable, correct types.
- **Three stale `__init__.py` exports identified:** `YahooCompany`, `YahooFinancials`, `YahooMarketData` — zero external callers. These are implementation details of `YahooFinanceProvider` that leaked into the public API.

**Sprint 146 recommended target:** Remove `YahooCompany`, `YahooFinancials`, `YahooMarketData` from `atlas/providers/__init__.py`. Types stay in `yahoo.py`; only their public-API surface is tightened. Zero external callers confirmed. Low risk.

---

## 2026-07-02: Sprint 144 — Close Decision Cleanup Track

Decision: Formally close the `atlas/decision/` cleanup track after Sprints 142–144. No further cleanup sprints planned until a new dead-code finding or clear successor architecture emerges.

**Rationale:** After package inventory (Sprint 142), dead renderer deletion (Sprint 143), export verification, and release guardrails, the decision package contains only active, intentional modules. All 5 `__init__.py` exports are healthy. All 7 modules have clear responsibilities. No stale imports. No dead code. Further cleanup would create churn without architectural benefit.

**Final stable package:** `__init__.py`, `decision_engine.py`, `decision_context.py`, `decision_result.py`, `decision_renderer.py`, `comparison.py`, `memory.py`.

**Why `decision_engine.py` remains:** Foundational composition engine. Single external production caller (`atlas/intelligence/engine.py`). Composes portfolio fit, comparison, watchlist intelligence, and memory. No Blueprint-aligned successor yet.

**Why `comparison.py` remains:** Canonical comparison location since Sprint 103. Active symbols: `ComparisonCandidate`, `ComparisonRanking`, `ComparisonResult`, `compare_tickers`. Dead renderer path deleted Sprint 143. Clean.

**Why `memory.py` remains:** Canonical memory/history location since Sprint 104. CLI `atlas memory save/show/compare` commands depend on it. All 7 public symbols active.

**Reopening condition:** Reopen when a new zero-caller dead function is found, when `decision_engine.py` has a clear Blueprint-aligned successor, or when the package accumulates new stale migration residue.

**Sprint 145 recommended target:** Provider boundary audit — inspect `atlas/providers/` for stale symbols, dead provider implementations, or boundary violations following the same audit-first pattern.

---

## 2026-07-02: Sprint 143 — Delete Dead Decision Comparison Renderer

Decision: Delete `render_comparison_result`, `_render_ranking`, and `_ranking_score` from `atlas/decision/comparison.py`. Zero external callers confirmed by repo-wide grep.

**Zero-caller audit findings:**
- `render_comparison_result`: only hit was its own definition and internal calls to `_render_ranking`. Zero external production callers. Zero CLI surface.
- `_render_ranking`: only called by `render_comparison_result` (now deleted).
- `_ranking_score`: only called by `_render_ranking` (now deleted).

**Changes:** 3 functions deleted (~45 lines). `comparison.py` reduced from 186 to ~141 lines. Active API (`ComparisonCandidate`, `ComparisonRanking`, `ComparisonResult`, `compare_tickers`) unchanged. Sprint 142 guardrail updated: `test_sprint142_render_comparison_result_is_importable` → `test_sprint143_render_comparison_result_deleted`. Docs updated.

**Behavior changes:** None. Comparison ranking, decision engine, CLI, memory, and all other behavior unchanged.

**Sprint 144 recommended target:** Decision package release checkpoint — verify the decision package is stable, confirm no further cleanup warranted, and close the decision cleanup track.

---

## 2026-07-02: Sprint 142 — Decision Package Cleanup Checkpoint

Decision: Begin `atlas/decision/` cleanup track with an audit-only sprint. No runtime changes.

**Findings:**
- 7 modules, 1010 lines total.
- All 5 `__init__.py` exports are active and intentional.
- `decision_engine.py` (474 lines): foundational — composes portfolio fit, comparison, watchlist intelligence, memory. No stale imports.
- `decision_context.py` (23 lines): clean frozen DTO. `Portfolio` TYPE_CHECKING-guarded.
- `decision_result.py` (42 lines): clean frozen DTO. `PortfolioFitResult` TYPE_CHECKING-guarded.
- `decision_renderer.py` (32 lines): active utility.
- `comparison.py` (186 lines): canonical comparison location (migrated from `atlas.analysis.comparison` Sprint 103). **`render_comparison_result` is dead — zero external callers.** `_render_ranking` and `_ranking_score` are also dead (only called by `render_comparison_result`).
- `memory.py` (238 lines): canonical memory/history location (migrated from `atlas.analysis.memory` Sprint 104). All 7 public symbols active.
- Stale import audit: zero stale production imports. All stale symbol hits are guardrail tests or docstring migration notes.
- Blueprint overlap: `atlas/domains/decision/` has same-named types (`DecisionContext`, `DecisionResult`) but different purpose and shape. No migration warranted.

**Sprint 143 recommended target:** Delete `render_comparison_result`, `_render_ranking`, `_ranking_score` from `atlas/decision/comparison.py` — zero external callers, ~45 dead lines, no CLI surface, no behavior change.

---

## 2026-07-02: Sprint 141 — Close Analysis Cleanup Track

Decision: Formally close the `atlas/analysis/` cleanup track after Sprints 100–141. No further cleanup sprints are planned until `engine.py` has a clear successor architecture.

**Rationale:** After portfolio deletion (Sprints 128–135), placeholder consolidation (Sprint 139), export verification (Sprint 140), and deleted-module guardrails, the remaining analysis package contains only active, intentional modules. All 12 `__init__.py` exports are healthy. All deleted modules are verified gone. Further cleanup would create churn without architectural benefit.

**Final stable package:** `__init__.py`, `company_analysis.py`, `engine.py`, `explanation.py`, `report.py`, `scores.py`. No stale exports. No dead modules.

**Why `engine.py` remains:** 10 external production callers. It is the primary scoring engine for the entire analysis layer. No safe migration path until a Blueprint-aligned successor is designed with a clear caller migration plan.

**Why `scores.py` remains:** 10 external production callers across 6 packages. A 2-line utility; moving it creates churn for zero benefit. It is a permanent shared utility.

**Reopening condition:** Reopen this track when `engine.py` has a clear Blueprint-aligned successor and fewer than 10 active callers remain on the legacy path, or when a new batch of zero-caller modules is identified.

**Sprint 142 recommended target:** Decision package cleanup checkpoint — audit `atlas/decision/` for dead code, stale symbols, or consolidation candidates following the same audit-first pattern used for `atlas/analysis/`.

---

## 2026-07-02: Sprint 140 — Analysis Package Release Candidate Checkpoint

Decision: Audit-only sprint. No runtime behavior changed. `atlas/analysis/` confirmed at 6 modules. Sprint 138 module inventory corrected: `comparison.py` was deleted Sprint 103; `investment.py` never existed; the true remaining modules are `company_analysis.py`, `engine.py`, `explanation.py`, `report.py`, `scores.py`, `__init__.py`.

**Findings:**
- `atlas/analysis/__init__.py`: 12 exports, all active and intentional. No stale exports.
- `company_analysis.py`: clean post-Sprint 139. All 7 placeholder types and factories present. No imports from deleted submodules.
- `engine.py`: 230 lines. 10 external production callers. Foundational — do not migrate.
- `explanation.py`: 199 lines. `InvestmentExplanation`, `explain_investment_report`, `render_investment_explanation`. 1 external production caller (`atlas/decision/memory.py`). Active utility.
- `report.py`: 39 lines. `build_investment_report`, `render_investment_report`. 2 external production callers (`atlas/cli/main.py`, `atlas/comparison/engine.py`). Active utility.
- `scores.py`: 2 lines. `clamp_score`. 10 external production callers across 6 packages. Shared utility — do not move.
- All historically deleted modules confirmed not importable (watchlist, comparison, memory, scoring, portfolio, 7 placeholder submodules).
- All deleted legacy portfolio symbols confirmed absent (PortfolioIntelligenceEngine, PortfolioAnalysis, PortfolioSignal, PortfolioRecommendation, CompanyPortfolioProfile).

**Changes:** 1 new guardrail test file (`tests/test_analysis_package_sprint140.py`, 7 tests). 4 docs updated. No production code changed.

**Sprint 141 recommended target:** Close the analysis cleanup track. The `atlas/analysis/` package is clean and stable. No further consolidation is warranted. Sprint 141 should document the track closure in DecisionLog and update the status line to reflect that the analysis cleanup is complete.

---

## 2026-07-02: Sprint 139 — Consolidate 7 placeholder analysis submodules into company_analysis.py

Decision: Inline `GrowthAnalysis`, `MacroAnalysis`, `MoatAnalysis`, `QualityAnalysis`, `SentimentAnalysis`, `TechnicalAnalysis`, `ValuationAnalysis` (and their `placeholder_*` factories) from 7 separate 18-line files into `atlas/analysis/company_analysis.py`. Delete the 7 source files.

**Zero-caller audit findings:**
- All 7 modules (`growth.py`, `macro.py`, `moat.py`, `quality.py`, `sentiment.py`, `technicals.py`, `valuation.py`) had zero external callers outside `company_analysis.py` itself. All 7 types were already re-exported through `company_analysis.py`; no production file imported from the submodules directly.

**Changes:** 7 placeholder type/factory pairs inlined into `company_analysis.py`; 7 source files deleted; `tests/test_company_analysis.py` imports consolidated + 4 Sprint 139 guardrail tests added; 4 docs updated. `atlas/analysis/` reduced from 13 modules to 6.

**Why this was safe:** Identical structure across all 7 modules (same 4-field frozen dataclass, one factory). Zero external import surface. Consolidation removes indirection without changing any behavior or value.

**Sprint 140 recommended target:** Analysis package release candidate checkpoint — audit remaining 6 modules (`company_analysis.py`, `comparison.py`, `engine.py`, `investment.py`, `scores.py`, `__init__.py`), confirm no stale exports, and assess whether any additional consolidation is warranted before closing out the `atlas/analysis/` cleanup track.

---

## 2026-07-02: Sprint 132 — Delete PortfolioAnalysis, PortfolioSignal, PortfolioRecommendation

Decision: Delete `PortfolioAnalysis`, `PortfolioSignal`, and `PortfolioRecommendation` from `atlas/analysis/portfolio.py`. Confirmed zero active production callers after Sprint 131 migrated the last dependency (`reasoning/engine.py`).

**Zero-caller audit findings:**
- `PortfolioAnalysis`: all hits outside `portfolio.py` were test fixture imports, docstring comments (in `atlas/capabilities/portfolio_intelligence/models.py`), stale string literals (`atlas/cli/deprecations.py`), and re-exports (`atlas/analysis/__init__.py`). Zero production import sites.
- `PortfolioSignal`: all hits were field type annotations within `PortfolioAnalysis` (also deleted) and stale test assertions. Zero production import sites.
- `PortfolioRecommendation`: all hits were `PortfolioAnalysis.recommendation` field type (deleted), docstring comment in models.py, stale string in deprecations.py, and stale re-export in `__init__.py`. Zero production import sites.

**Changes:** `PortfolioSignal`, `PortfolioRecommendation`, `PortfolioAnalysis` classes deleted; unused `from enum import Enum` removed; `PortfolioAnalysis`/`PortfolioRecommendation` removed from `atlas/analysis/__init__.py`; 8 new Sprint 132 guardrail tests added; stale "importable" assertions flipped across 7 test files. `portfolio.py` reduced from 109 to 69 lines.

**Why `Portfolio`, `PortfolioPosition`, `CompanyPortfolioProfile` remain:** `Portfolio` and `PortfolioPosition` are the CLI JSON-loading boundary (5 commands in `cli/main.py`); `CompanyPortfolioProfile` is the provider contract type (`providers/base.py`, `providers/mock.py`, `providers/yahoo.py`) — HIGH risk to migrate atomically.

**Sprint 133 recommended target:** Migrate `CompanyPortfolioProfile` from providers to `PortfolioFitInput`. Requires updating 3 provider files simultaneously.

## 2026-07-02: Sprint 131 — Migrate ReasoningInput.portfolio_analysis to PortfolioFitResult

Decision: Retype `ReasoningInput.portfolio_analysis` in `atlas/reasoning/engine.py` from `PortfolioAnalysis | None` to `PortfolioFitResult | None`. Remove TYPE_CHECKING guard entirely. Update all field accesses.

**Rationale:** `PortfolioAnalysis` had zero production runtime callers after Sprint 118 moved it behind `TYPE_CHECKING`. The field `ReasoningInput.portfolio_analysis` was typed as `PortfolioAnalysis | None` but is never populated in production — intelligence and decision engines pass `PortfolioFitResult` to their own result types. Retyping to `PortfolioFitResult` removes the last production-facing `PortfolioAnalysis` dependency.

**Field mapping applied:**
- `.final_reasoning` → `.summary` (PortfolioFitResult field)
- `.portfolio_score` → `.fit_score` (PortfolioFitResult field)
- `.sector_concentration.reasoning` → `.sector_concentration.note` (PortfolioFitDimension field)

**Changes:** TYPE_CHECKING import block removed; `PortfolioFitResult` added as runtime import; `ReasoningInput.portfolio_analysis` retyped; 6 guardrail tests added; `PORTFOLIO_ENGINE_CALLERS` is now empty (all 5 callers migrated across Sprints 124–131).

**Result:** `PortfolioAnalysis`, `PortfolioSignal`, and `PortfolioRecommendation` are now test-only with zero production callers. Deletion candidates for Sprint 132.

**Sprint 132 recommended target:** Delete `PortfolioAnalysis`, `PortfolioSignal`, `PortfolioRecommendation` from `atlas/analysis/portfolio.py` and `atlas/analysis/__init__.py`. Also update stale `atlas/cli/deprecations.py` string that references `atlas/reasoning/engine.py (PortfolioAnalysis)`.

## 2026-07-02: Sprint 130 — Delete Dead Portfolio Private Helpers

Decision: Delete 16 dead private helper functions and `get_mock_company_portfolio_profile` from `atlas/analysis/portfolio.py`. Confirmed zero active callers repo-wide before deletion.

**Zero-caller audit findings:**
- All 16 helper name hits in `atlas/capabilities/portfolio_intelligence/engine.py` are independently-defined functions in that module — not imports from or calls to the legacy helpers.
- `_weighted_average` hit in `suitability/engine.py` is that file's own local function.
- `get_mock_company_portfolio_profile` had stale imports only (both tests that called it deleted Sprint 128).

**Changes:** 16 private helpers deleted; `get_mock_company_portfolio_profile` deleted; unused `CompanyDataProvider` import removed; stale test imports removed; `__init__.py` export removed. `portfolio.py` reduced from ~350 to 109 lines.

**Sprint 131 recommended target:** Migrate `PortfolioAnalysis` out of `reasoning/engine.py` — retype `ReasoningInput.portfolio_analysis` as `PortfolioFitResult | None`, update duck-typed field accesses. After Sprint 131, `PortfolioAnalysis`, `PortfolioSignal`, `PortfolioRecommendation` become deletion candidates.

## 2026-07-02: Sprint 129 — Remaining Portfolio Legacy Symbol Audit

Decision: Audit all remaining public symbols in `atlas/analysis/portfolio.py`. No deletions this sprint. Sprint 130 target selected.

**Findings:**
- 7 public symbols remain: `Portfolio`, `PortfolioPosition`, `PortfolioSignal`, `PortfolioRecommendation`, `PortfolioAnalysis`, `CompanyPortfolioProfile`, `get_mock_company_portfolio_profile`
- 16 private helpers are dead code (zero callers since `PortfolioIntelligenceEngine` deleted)
- `get_mock_company_portfolio_profile` has zero active callers (stale import only)
- `PortfolioAnalysis` annotation-only in `reasoning/engine.py`; `ReasoningInput.portfolio_analysis` field never populated in production — test-fixture-only usage
- `PortfolioRecommendation` zero production callers; only used as `PortfolioAnalysis.recommendation` field type
- `PortfolioSignal` zero external callers; only used as `PortfolioAnalysis` field types
- `CompanyPortfolioProfile` deeply coupled to 3 provider files — HIGH risk to migrate
- `Portfolio` (legacy) CLI boundary: `Portfolio.from_json_file` in `cli/main.py` (5 commands)

**Sprint 130 target:** Delete 16 dead private helpers + `get_mock_company_portfolio_profile`. Zero behavior change. Reduces `portfolio.py` from ~350 to ~90 lines.

## 2026-07-02: Sprint 128 — Delete PortfolioIntelligenceEngine

Decision: Delete `PortfolioIntelligenceEngine` class from `atlas/analysis/portfolio.py` and remove its re-export from `atlas/analysis/__init__.py`. Zero active production callers confirmed as of Sprint 127.

**Audit finding:** `grep -rn "PortfolioIntelligenceEngine"` across the repo found zero active production callers after Sprints 124–127 migrated all 4 engine call sites (decision, intelligence, conversation, dashboard) to `PortfolioIntelligenceCapability`. Remaining hits were test files and documentation strings only.

**Deletion scope:** Only the `PortfolioIntelligenceEngine` class (lines 85–145 in the pre-deletion file). All shared types — `Portfolio`, `PortfolioPosition`, `PortfolioAnalysis`, `PortfolioSignal`, `PortfolioRecommendation`, `CompanyPortfolioProfile`, `get_mock_company_portfolio_profile` — remain intact. Private helper functions (`_diversification_impact`, `_sector_concentration`, etc.) become dead code but are left in place for this sprint.

**Test cleanup:** Deleted `test_portfolio_engine_analyzes_target_in_portfolio_context` and `test_portfolio_engine_penalizes_existing_holding_overlap` (test_portfolio.py), deleted `test_portfolio_engine_can_analyze_ticker_from_provider` (test_providers.py). Rewrote `test_sprint118_reasoning_portfolio_analysis_field_still_accepted` to construct `PortfolioAnalysis` directly. Updated 8 stale "engine importable" assertions across sprint-guardrail tests to either remove the check or flip to assert NOT importable.

**Guardrails added:** 3 new tests in `test_portfolio_analyze_deprecation.py` (Sprint 128 block) confirm: `PortfolioIntelligenceEngine` raises `ImportError` from `atlas.analysis.portfolio`, is absent from `atlas.analysis` namespace, and shared types remain importable.

**Remaining `atlas.analysis.portfolio` runtime coupling:** `cli/main.py` (Portfolio loading), `adapters/portfolio.py` (LegacyPortfolio adapter), `providers/` (CompanyPortfolioProfile), `portfolio_review/engine.py` (structural analysis), `reasoning/engine.py` (PortfolioAnalysis duck-typing). These are out of scope for Sprint 128.

## 2026-07-02: Sprint 127 — Dashboard Engine: Remove Stale portfolio_engine Attribute; PortfolioIntelligenceEngine Zero-Caller Milestone

Decision: Remove the dead `self.portfolio_engine` / `portfolio_engine` constructor parameter
from `atlas/dashboard/engine.py`. Option A + B (dead-code removal + Portfolio to TYPE_CHECKING).

**Audit finding:** `self.portfolio_engine = portfolio_engine or PortfolioIntelligenceEngine()`
was assigned at construction but never read anywhere in the file. `_portfolio_section`
target-fit block was fully migrated to `self.portfolio_fit_capability` in Sprint 115.
After that migration, the legacy attribute had zero active call sites.

**`PortfolioIntelligenceEngine` zero-caller milestone reached:** After Sprint 127, no production
engine in the Atlas codebase imports or instantiates `PortfolioIntelligenceEngine`. It remains
in `atlas/analysis/portfolio.py` and is re-exported by `atlas/analysis/__init__.py`, but has
no active callers. Sprint 128 is the designated deletion sprint.

**Remaining `atlas.analysis.portfolio` active imports:** `cli/main.py` (Portfolio loading),
`adapters/portfolio.py` (LegacyPortfolio adapter), `providers/` (CompanyPortfolioProfile),
`portfolio_review/engine.py` (structural analysis). These are out of scope for Sprint 127.

## 2026-07-02: Sprint 126 — Conversation Engine: Remove Stale portfolio_engine Attribute

Decision: Remove the dead `self.portfolio_engine` / `portfolio_engine` constructor parameter
from `atlas/conversation/engine.py`. This is Option A (pure dead-code removal).

**Audit finding:** `self.portfolio_engine = portfolio_engine or PortfolioIntelligenceEngine()`
was assigned at construction but never read anywhere in the file. `_answer_portfolio_review`
was fully migrated to `self.portfolio_fit_capability` in Sprint 114. After Sprint 125 updated
the `IntelligenceEngine(...)` call to use `portfolio_fit_capability=`, no code in the engine
accessed `self.portfolio_engine`. It was a zombie attribute.

**Changes:** `PortfolioIntelligenceEngine` import removed; `portfolio_engine` constructor
parameter removed; `self.portfolio_engine` assignment removed; `Portfolio` moved to
TYPE_CHECKING (annotation-only on `ConversationInput.portfolio`); `from __future__ import
annotations` added.

**No behavior change** — the removed attribute had no active call sites.

**Remaining `PortfolioIntelligenceEngine` runtime caller:** `atlas/dashboard/engine.py` only.

## 2026-07-02: Sprint 125 — Intelligence Engine: PortfolioIntelligenceEngine → PortfolioIntelligenceCapability

Decision: Migrate `atlas/intelligence/engine.py` from legacy `PortfolioIntelligenceEngine`
to Blueprint-aligned `PortfolioIntelligenceCapability`. Option D (tiny runtime migration)
chosen — same pattern as Sprint 124, all field mappings are 1:1.

**Adapter chain:** same pattern as decision engine — `provider.get_portfolio_profile(ticker)`
→ `portfolio_fit_input_from_profile(profile)` → `legacy_portfolio_to_domain_portfolio(portfolio)`
→ `capability.analyze(domain_portfolio, fit_input)`.

**Field mappings:** `portfolio_score` → `fit_score`; `.reasoning` → `.note` on all 7 dimensions;
`overlap_with_existing_holdings` → `overlap`; `diversification_impact` → `diversification`;
`expected_portfolio_quality_impact` → `quality_impact`; `expected_portfolio_risk_impact` → `risk_impact`.

**`IntelligenceReport.portfolio_analysis`:** field name kept for caller compatibility; type
annotation updated to `PortfolioFitResult`.

**`conversation/engine.py` side-effect fix:** the `IntelligenceEngine(portfolio_engine=...)` kwarg
was stale after `IntelligenceEngine` dropped that parameter. Updated to pass
`portfolio_fit_capability=self.portfolio_fit_capability` instead. `conversation/engine.py`
retains its own `self.portfolio_engine` (legacy) for its own `_answer_portfolio_review` path.

**No behavior change** for the no-portfolio path. Portfolio impact text wording changes slightly
(`.note` framing vs `.reasoning` framing) — this is the intended Blueprint-layer framing,
consistent with all prior migrations.

## 2026-07-02: Sprint 124 — Decision Engine: PortfolioIntelligenceEngine → PortfolioIntelligenceCapability

Decision: Migrate `atlas/decision/decision_engine.py` from legacy `PortfolioIntelligenceEngine`
to Blueprint-aligned `PortfolioIntelligenceCapability`. Use `fit_score < 55` as the unified
poor-fit boundary, replacing both legacy guards.

**Recommendation guard replacement:** The legacy code used two sequential guards:
1. `if portfolio_analysis.recommendation.value in {"Avoid", "Reduce"}` (fires when `portfolio_score < 50`)
2. `if portfolio_analysis.portfolio_score < 55: return WATCH`

`PortfolioFitResult` intentionally omits the recommendation enum. Both guards are consolidated
into a single `if portfolio_fit_result.fit_score < 55` check, returning WATCH (atlas_score ≥ 75)
or AVOID (atlas_score < 75).

**Documented behavior change:** Scores in [50, 54] previously returned WATCH only (old guard 1
did not fire for NEUTRAL recommendation; old guard 2 fired unconditionally returning WATCH).
New code returns WATCH or AVOID based on `atlas_score`. This is a slightly stronger response
for well-scored tickers with poor portfolio fit. Scores ≥ 55 are unaffected.

**Field mappings:** `portfolio_score` → `fit_score`, `final_reasoning` → `summary`,
`overlap_with_existing_holdings` → `overlap`. Dimension `.score` and `.note` unchanged.

**Constructor:** `portfolio_engine: PortfolioIntelligenceEngine` → `portfolio_fit_capability:
PortfolioIntelligenceCapability`. `atlas/intelligence/engine.py` updated to drop stale
`portfolio_engine=` kwarg from its `AtlasDecisionEngine(...)` call (retains its own
`self.portfolio_engine` for `_optional_portfolio_analysis`).

**`decision_result.py`:** `portfolio_analysis` field annotation updated from `PortfolioAnalysis`
to `PortfolioFitResult`; field name kept for external caller compatibility.

## 2026-07-02: Sprint 123 — Decision Layer Portfolio Audit: Partial TYPE_CHECKING Cleanup

Decision: `decision_context.py` and `decision_result.py` annotation-only imports moved behind
TYPE_CHECKING. `decision_engine.py` runtime coupling retained unchanged.

`decision_context.py`: `Portfolio` is used only as a type annotation on `DecisionContext.portfolio`.
No runtime field access anywhere in the file. Moved behind TYPE_CHECKING.

`decision_result.py`: `PortfolioAnalysis` is used only as a type annotation on
`DecisionResult.portfolio_analysis`. No runtime field access. Moved behind TYPE_CHECKING.

`decision_engine.py`: `PortfolioIntelligenceEngine` is instantiated at line 24 and called via
`analyze_ticker()` at line 116. `PortfolioAnalysis` is accessed for `.portfolio_score`,
`.final_reasoning`, `.recommendation.value`, `.sector_concentration.score`,
`.country_concentration.score`, `.market_cap_concentration.score`,
`.overlap_with_existing_holdings.score`. Not safe to touch without full behavioral parity.

Blocker for Sprint 124: `portfolio_analysis.recommendation.value` is used to gate action
selection (`if portfolio_analysis.recommendation.value in {"Avoid", "Reduce"}`). `PortfolioFitResult`
intentionally omits the recommendation enum (no advisory semantics in Blueprint layer). Sprint 124
must decide: drop the guard, introduce a compatibility score threshold, or retain the enum.

## 2026-07-02: Sprint 122 — Home Portfolio Dependency: TYPE_CHECKING Only (Option D)

Decision: `atlas/home/engine.py` imports `Portfolio` only for the `AtlasHomeInput.portfolio`
field annotation. No runtime field access occurs inside the engine — the value is only
None-checked and passed through to `PortfolioReviewInput`. Migration is TYPE_CHECKING guard
(Option D): `from __future__ import annotations` + `if TYPE_CHECKING: from atlas.analysis.portfolio import Portfolio`.

Rationale: Purest possible annotation-only case. No duck-typed field access, no logic change,
no caller impact. Zero risk. Same pattern as Sprints 118, 119 (partial), 121.

## 2026-07-02: Sprint 121 — Monitoring Portfolio Dependency: TYPE_CHECKING Only (Option D)

Decision: `atlas/monitoring/engine.py` imports `Portfolio` for method type annotations only.
No `PortfolioAnalysis` or `PortfolioIntelligenceEngine` imports present. Migration strategy
is TYPE_CHECKING guard (Option D): `from __future__ import annotations` + `if TYPE_CHECKING:
from atlas.analysis.portfolio import Portfolio`. All runtime attribute access (`.positions`,
`.ticker`, `.weight`, `.sector`, `.country`, `.quality_score`, `.risk_score`) is duck-typed
and requires no import. All callers (cli, dashboard, portfolio_review) continue passing
legacy Portfolio objects unchanged.

Rationale: Option A (shared Portfolio migration) would require migrating all three callers
simultaneously — `cli/main.py`, `dashboard/engine.py`, and `portfolio_review/engine.py` — which
is out of scope for Sprint 121. Option D achieves the boundary goal (no runtime import from
legacy module) with zero behavior change and zero caller breakage.

## 2026-06-29: Keep Sprint 36 as a Foundation Sprint

Decision: establish boundaries, canonical entities, docs, CI, hooks, and AI
interfaces without rewriting existing engines.

Rationale: Atlas already has working deterministic engines. A large migration
would add risk without improving the investor experience.

## 2026-06-29: Use Python Backend as the Source of Truth

Decision: keep existing backend code under `atlas/` and document `backend/` as
the backend boundary.

Rationale: this preserves all existing APIs and test coverage while making the
repository easier to navigate.

## 2026-06-29: Add Strict TypeScript Configuration Before Frontend Code

Decision: add `frontend/tsconfig.json` and `frontend/package.json` with strict
type checking, but no frontend runtime.

Rationale: future UI work should start from strong defaults without forcing an
application framework too early.

## 2026-06-29: Define AI as Interfaces First

Decision: create `atlas.ai` protocols for reasoning, knowledge, summary,
discovery, and decision support services.

Rationale: Atlas should remain deterministic and explainable until concrete AI
services can be evaluated against the Constitution.

## 2026-06-29: Build Portfolio as the First Real Domain

Decision: implement deterministic portfolio calculations, validation, and
structured observations inside `atlas.domains.portfolio`.

Rationale: portfolio understanding is foundational to Atlas. A portfolio is not
just a list of positions; it is a collection of investment decisions. The domain
therefore starts with value, allocation, concentration, and data quality before
any user-facing action language.

## 2026-06-29: Separate Decision Reasoning From Recommendations

Decision: add `atlas.domains.decision` as a non-advisory reasoning foundation
instead of modifying the older action-oriented `atlas.decision` package.

Rationale: Sprint 38 is about evidence, observations, unknowns, confidence, and
explainability. Keeping the new domain separate preserves existing behavior and
gives future AI services a deterministic reasoning contract.

## 2026-06-30: Model Knowledge as Attributed Facts

Decision: implement `atlas.domains.knowledge` as immutable nodes, edges,
facts, sources, references, and deterministic queries.

Rationale: Atlas knowledge should be structured evidence, not generated
opinion. The domain should remain independent of AI providers, vector databases,
and graph storage so future Portfolio, Research, Decision Engine, and AI layers
can share the same factual foundation.

## 2026-06-30: Model Research as Structured Understanding

Decision: implement `atlas.domains.research` as research projects, notes,
questions, assumptions, evidence references, thesis fragments, summaries, and
validation.

Rationale: research should connect curiosity, evidence, assumptions, and open
questions before Atlas reaches conclusions. Keeping Research independent of AI,
UI, persistence, providers, and recommendations preserves the Blueprint
principle that understanding comes before judgment.

## 2026-06-30: Build Company Analysis as a Capability

Decision: implement `atlas.capabilities.company_analysis` as a consumer of
Company, Knowledge, Research, and Decision structures rather than as a new
domain owner.

Rationale: Company Analysis should organize existing structured evidence into
explainable business understanding. Keeping it in `atlas.capabilities` prevents
it from owning Knowledge, Research, or Decision responsibilities and preserves
the Blueprint principle that Atlas helps investors understand businesses before
forming conviction.

## 2026-06-30: Build Watchlist Intelligence as Structured Observation

Decision: implement `atlas.capabilities.watchlist_intelligence` as a consumer of
Research, Knowledge, and Company Analysis structures rather than as a domain
owner.

Rationale: a watchlist should help investors track unanswered questions without
creating noise or trading behavior. Keeping Watchlist Intelligence in
`atlas.capabilities` preserves clean domain ownership and reinforces the
Blueprint principle that Atlas supports understanding before action.

## 2026-06-30: Build Discovery as Structured Curiosity

Decision: implement `atlas.capabilities.discovery` as a deterministic consumer
of Knowledge, Research, Company Analysis, and Watchlist Intelligence structures.

Rationale: Discovery should help investors decide what deserves further study,
not what action to take. Keeping it in `atlas.capabilities` preserves domain
ownership boundaries and aligns with the Blueprint principle that discovery is
the disciplined pursuit of understanding before conviction.

## 2026-06-30: Introduce `atlas.adapters` as the Legacy-to-Domain Bridge

Decision: add `atlas.adapters.portfolio.legacy_portfolio_to_domain_portfolio`
and a new, additive `atlas portfolio summary` CLI command that calls
`atlas.domains.portfolio` directly, instead of rewriting the existing
`atlas portfolio analyze`/`atlas portfolio review` commands.

Rationale: the legacy CLI portfolio file format
(`atlas.analysis.portfolio.Portfolio`, positions with a relative `weight`
and no absolute market value) answers a different question (ticker-fit
analysis, CIO review with provider/profile/market dependencies) than the
Portfolio Domain (portfolio understanding: allocation, concentration,
validation). Forcing the existing commands onto the domain would have been
a disguised behavior change, not a safe migration. Adding `atlas.adapters`
as the one layer permitted to import both legacy and domain code lets the
CLI begin exercising `atlas.domains.portfolio` today, on a read-only path,
without touching the two existing commands or their output. Architecture
boundary tests were updated so domains may never import adapters back,
keeping the dependency direction one-way (legacy/CLI -> adapters -> domains).

## 2026-06-30: Augment, Don't Replace, `atlas portfolio analyze`

Decision: extend `atlas portfolio analyze` to additionally print a Portfolio
Domain summary (allocation, concentration, cash weight, top holdings) using
the Sprint 45 adapter, while leaving `PortfolioIntelligenceEngine`'s
proprietary ticker-fit scoring (diversification impact, sector/country/
market-cap concentration impact, overlap, expected quality/risk impact, and
the `Strong Add`/`Add`/`Neutral`/`Reduce`/`Avoid` recommendation) completely
unchanged.

## 2026-07-01: Add Capability JSON Export Commands (Sprint 51)

Decision: add `atlas watchlist intelligence [--output FILE]` and
`atlas discovery export [--output FILE]` as the first capability export
commands, backed by new `exporter.py` modules in each capability package that
serialize the capability's native report type to a JSON dict matching the
Sprint 50 Daily Brief input format.

Rationale: Sprint 50 added Daily Brief `--watchlist` and `--discovery` CLI
flags that accept local JSON files, but users had to author those files manually.
Sprint 51 closes this gap by adding export commands that produce JSON in exactly
the format the loaders expect, enabling a fully deterministic local workflow
with no manual JSON authoring required. The exporters are pure functions with no
side effects; the CLI commands produce human-readable output by default and write
JSON only when `--output` is supplied, preserving the useful plain-text output
path. Both commands run on empty inputs (no watchlist items, no discovery inputs)
which produces valid structural JSON that Daily Brief can consume — wiring real
structured inputs to the export commands is deferred to Sprint 52.

## 2026-07-01: Extend Daily Brief CLI with Local JSON Input Flags (Sprint 50)

Decision: add `--research`, `--watchlist`, `--discovery`, and `--company-analysis`
flags to `atlas daily summary`, backed by a new `json_loader.py` module that
parses local JSON files into lightweight structured types the Daily Brief engine
can consume, and route those parsed objects through the Sprint 49 `build_daily_brief_input`
builder before calling `DailyBriefCapability.generate()`.

Rationale: the Sprint 49 capability integration proved all five input types work
correctly at the library level. Sprint 50 closes the gap between capability-level
integration and runtime usability without requiring a full JSON serialisation
round-trip for existing Atlas capability outputs. Each flag reads a local file
only, validates the JSON shape enough to fail cleanly on bad input, and makes no
network calls. The `json_loader.py` module uses minimal dataclasses (not the full
typed Atlas models) because the engine already uses duck-typed `getattr` access —
this keeps the loader self-contained, easy to test, and easy to extend. The
`--portfolio` flag was already present from Sprint 48; the four new flags follow
the same additive pattern.

## 2026-07-01: Connect Daily Brief to Typed Atlas Structures (Sprint 49)

Decision: create `atlas.capabilities.daily_brief.input_builder.build_daily_brief_input`
as the canonical adapter from typed Atlas structures to `DailyBriefInput`, and fix
five attribute-name mismatches in the engine that prevented correct output when real
typed objects were supplied.

Rationale: Sprint 48's engine used duck typing (`getattr` with fallback) to consume
inputs, but several attribute names were wrong for the real Atlas types — `ticker`
instead of `title` for `ResearchNote`, `suggested_next_steps` instead of
`suggested_next_research_steps` for `WatchlistIntelligenceReport`, `reason` instead
of `reasons[0].detail` for `DiscoveryCandidate`, `ticker` instead of `company.ticker`
and `evidence_gaps` instead of `evidence_links` for `CompanyAnalysisReport`. The
mismatches were silent (the fallback values suppressed them) but would have produced
wrong output in production. The input builder adds a typed, keyword-only interface
that documents what Atlas structures are accepted, extracts `ResearchProject` open
questions automatically, and is easy to test. No new data sources were introduced;
all inputs come from existing Atlas domains and capabilities.

## 2026-07-01: Add Daily Brief as a Blueprint-Aligned Capability

Decision: create `atlas.capabilities.daily_brief` as a new capability
alongside `company_analysis`, `watchlist_intelligence`, and `discovery`,
and wire it to a new `atlas daily summary` CLI command, while leaving the
legacy `atlas.daily_brief` engine and `atlas daily brief` command
completely unchanged.

Rationale: a legacy Daily Brief engine (`atlas.daily_brief`) already
exists and is fully tested (8 tests, 6 sections, CIO-style multi-engine
output). Rather than rewriting it, Sprint 48 adds a parallel
Blueprint-aligned capability that accepts domain-native inputs
(`PortfolioSummary` from the Sprint 45 adapter, `ResearchNote`,
`KnowledgeCollection`, `CompanyAnalysisReport`, `WatchlistIntelligenceReport`,
`DiscoveryReport`) and produces a deterministic, calm, provider-free
`DailyBriefReport`. This preserves the existing CLI command's behavior
exactly, gives the Blueprint architecture its first Daily Brief path, and
sets up future sprints to extend `atlas daily summary` with additional
input flags as more domain-native JSON inputs become CLI-accessible.

## 2026-06-30: Augment, Don't Replace, `atlas portfolio review`

Decision: apply the same additive pattern from Sprint 46 to
`atlas portfolio review`: append a Portfolio Domain summary section to the
existing CIO-style review output rather than rewriting or replacing any
part of `PortfolioReviewEngine`.

Rationale: the legacy review engine combines investor profile, suitability,
risk drift, themes, market context, economics, monitoring, and principles
checks — none of which have a Portfolio Domain equivalent today. Replacing
any part of this logic would require new domain models (investor profile,
market regime, economics signals) that are out of scope. The
`PortfolioReviewEngine` depends on `atlas.analysis.portfolio.Portfolio`
(the legacy type), not `atlas.shared.Portfolio`, so it cannot be swapped
for domain-native calls without a larger migration. The additive pattern is
safe, reversible, and brings all three `portfolio` CLI commands
(`summary`, `analyze`, `review`) to a state where they exercise
`atlas.domains.portfolio` for the calculations it genuinely owns:
allocation, concentration, cash weight, and top holdings. The Sprint 45
adapter needed no changes for Sprints 46 or 47.

## 2026-06-30: Augment, Don't Replace, `atlas portfolio analyze`

Decision: extend `atlas portfolio analyze` to additionally print a Portfolio
Domain summary (allocation, concentration, cash weight, top holdings) using
the Sprint 45 adapter, while leaving `PortfolioIntelligenceEngine`'s
proprietary ticker-fit scoring completely unchanged.

Rationale: `atlas portfolio analyze` answers "how well would this new
ticker fit the existing portfolio" — a hypothetical-addition scoring
question with no Portfolio Domain equivalent. The Portfolio Domain
deliberately only answers "what does this portfolio currently look like."
Rewriting the fit-scoring math to route through the domain would require
either inventing domain concepts that don't belong there (target-weight
scoring, pro-forma exposure) or producing different numbers under a
different methodology, which would be a hidden behavior change disguised as
a migration. Appending the existing domain summary section is additive,
preserves every existing output byte exactly, and still proves the CLI
analyze path can pull from `atlas.domains.portfolio` for the parts that
genuinely overlap (allocation, concentration). The Sprint 45 adapter needed
no changes.

## 2026-07-01: Wire Real JSON Inputs to Capability Export Commands (Sprint 52)

Decision: add three adapter modules (`atlas/adapters/watchlist.py`,
`atlas/adapters/knowledge.py`, `atlas/adapters/research_input.py`) and extend
`atlas watchlist intelligence` with `--input` and `atlas discovery export` with
`--knowledge`, `--research`, `--watchlist` so both commands produce meaningful
structured output from local JSON files.

Rationale: Sprint 51's export commands ran on empty inputs, producing valid but
empty reports — no candidates, no open questions, no suggestions. This made the
end-to-end pipeline (`watchlist intelligence → discovery export → daily summary`)
structurally correct but semantically inert. Sprint 52 closes the gap by parsing
real watchlist items, knowledge facts, and research projects from local files and
routing them through the same deterministic engines. The adapter modules are placed
in `atlas/adapters/` (the only layer permitted to bridge legacy shapes and domain
types), remain side-effect-free, and raise ValueError with clear messages on
invalid input. `open_questions` in watchlist items are converted to
`ResearchProject` entries with `OPEN` `ResearchQuestion` objects so the
`WatchlistIntelligenceEngine` surfaces them as unresolved questions in its report —
consistent with how other Atlas inputs represent open questions. No existing CLI
command behavior was changed; all new flags are additive and optional.

## 2026-07-01: Add Research Export Command to Complete Daily Brief Pipeline (Sprint 53)

Decision: add `atlas/capabilities/daily_brief/research_exporter.py` with
`research_projects_to_dict()` and an `atlas research export [--input FILE]
[--output FILE]` CLI command that converts the adapter-format research projects
JSON (`{"projects": [...]}`) to the Daily Brief–compatible research JSON
(`{"notes": [...], "open_questions": [...]}`).

Rationale: Research notes and open questions were the only Daily Brief input
type that still required users to author JSON manually. Every other input type
(portfolio, watchlist, discovery, knowledge) already had a CLI export command
producing a file consumable by `atlas daily summary`. This sprint closes that
gap with a pure conversion step: `research_projects_from_dict` parses the input,
`research_projects_to_dict` serialises it to the daily brief format.
The exporter is placed in `atlas/capabilities/daily_brief/` (alongside the
other daily brief modules) because its output format is defined entirely by what
`parse_research_json` / the Daily Brief engine expect — it is a daily brief
concern, not a general research concern. No new domain models or capability
engines were introduced; this is a serialisation adapter only.

## 2026-07-01: Add Company Analysis Export Command to Complete Daily Brief Pipeline (Sprint 54)

Decision: add `atlas/capabilities/company_analysis/exporter.py` with
`company_report_to_dict` / `company_reports_to_list`, `atlas/adapters/company_analysis.py`
with `company_reports_from_dict`, and an `atlas company-analysis export [--input FILE]
[--output FILE]` CLI command under a new `company-analysis` subapp.

Rationale: Company analysis was the last Daily Brief input type that required users
to author JSON manually. The adapter accepts the same output format that the exporter
produces (self-consistent round-trip), so users can author company analysis JSON in
the export format, pass it to `atlas company-analysis export`, and consume the output
with `atlas daily summary --company-analysis`. When no input is provided the command
exports `[]` — an empty list that `parse_company_analysis_json` accepts and that
`build_daily_brief_input` treats as an empty tuple of company reports. `confidence`
accepts either a plain string (`"low"`) or a structured object with `level`,
`explanation`, `drivers`, and `limitations` fields, covering both quick authoring
and detailed structured input. The adapter reuses the existing `CompanyAnalysisReport`
model without invoking `CompanyAnalysisEngine` — the report is built directly from
user-supplied JSON fields without running deterministic risk / confidence scoring on
knowledge facts, since users may not have knowledge facts available at export time.

## 2026-07-01: Wire CompanyAnalysisEngine to Export Command (Sprint 55)

Decision: extend `atlas company-analysis export` with `--ticker`, `--knowledge`,
and `--research` flags that wire `CompanyAnalysisEngine.analyze()` to the
existing Sprint 54 export path, using the Sprint 52 adapters
(`knowledge_facts_from_dict`, `research_projects_from_dict`) for local input
parsing.

Rationale: Sprint 54's export command required users to author the full
company analysis JSON structure by hand. Sprint 55 closes this gap by letting
the engine derive observations, risks, evidence links, confidence, and
what-could-change content from local knowledge facts and research projects.
The `--ticker` flag is the minimum required input for the engine-backed path
because `CompanyAnalysisInput` requires a `Company` object with a ticker. When
`--research` is supplied, the first project matching the ticker topic is selected
as `research_project`; if none matches, the first project is used — this avoids
a hard failure for single-project research files where the topic may not exactly
match the ticker. The Sprint 54 `--input` path is preserved unchanged as a
separate branch in the same command, giving users two authoring options:
engine-backed (from structured local files) and manual (from a pre-authored
report JSON). No new adapter or exporter files were needed — only main.py was
modified, adding 40 lines to the existing command function.

## 2026-07-01: Add --company-name and --business-description to Company Analysis Export (Sprint 56)

Decision: add two optional string flags — `--company-name` and
`--business-description` — to `atlas company-analysis export`. Both populate
`CompanyAnalysisInput` fields used by `CompanyAnalysisEngine` without requiring
any network calls or new adapters.

Rationale: Sprint 55 always defaulted `Company.name` to the ticker string (e.g.
"AMD" instead of "AMD Corporation") and always left `business_description` empty,
causing a "Missing Business Description" unknown to appear in every engine report.
Both fields accept user-supplied local strings, require no external lookup, and
follow the existing pattern of optional CLI flags for local metadata. When
`--business-description` is supplied, `CompanyAnalysisEngine._unknowns()` no
longer appends the "Missing Business Description" unknown because
`business_description.strip()` is truthy. When `--company-name` is supplied,
`Company.name` is set to the user value; when omitted it falls back to the ticker
string. Both flags are entirely optional — omitting them preserves Sprint 55
behavior exactly.

## 2026-07-01: Add Company Analysis Merge Command (Sprint 60)

Decision: add `atlas company-analysis merge --inputs a.json --inputs b.json
--output combined.json` as a new subcommand under the existing
`company-analysis` subapp.

Rationale: Sprint 59's demo workflow used an inline `python3 -c` call to
concatenate two JSON lists. This was the only non-Atlas step in the pipeline.
The merge command removes that dependency, making the full multi-company demo
expressible in Atlas CLI commands only. The command operates at the raw JSON
dict level (load → validate via `parse_company_analysis_json` → concatenate
→ write) rather than deserialising into typed `CompanyAnalysisReport` objects,
because the inputs are already in the export format. `--inputs` accepts
repeated flags, so an arbitrary number of files can be merged. Input order is
preserved. The command validates each file before merging and fails cleanly on
missing files, invalid JSON, or non-object/non-list top-level values. No CLI
redesign to `atlas daily summary` was needed — `parse_company_analysis_json`
already accepts a JSON array of any length. 754 tests pass; 15 new tests in
`test_company_analysis_merge.py` cover command existence, two-file merge, order
preservation, single-file merge, Daily Brief compatibility, error handling,
no-network, and demo script correctness.

## 2026-07-01: Extend Demo to Two-Company Daily Brief (Sprint 59)

Decision: extend the Sprint 58 demo dataset from AMD-only to AMD + NVDA.
Updated `knowledge.json` (9 total facts), `research_input.json` (2 projects, 7
questions), and `watchlist_input.json` (2 items). Updated
`run_daily_brief_demo.sh` to generate separate company analysis exports for AMD
and NVDA, merge them via a Python one-liner into a single JSON array, and pass
the combined file to `atlas daily summary --company-analysis`. The Daily Brief
engine already accepts a JSON array of reports via `parse_company_analysis_json`,
so no CLI redesign was required. The merge step exposes a minor CLI limitation:
`--company-analysis` accepts one file, not multiple. This is documented as a
known limitation; Sprint 60 should address it. 739 tests pass; 34 tests in
`test_daily_brief_demo.py` (11 new vs Sprint 58) cover two-company data
validity, both company exports, merged array compatibility, two-company pipeline,
section presence, AMD/NVDA presence, two-report count, language safety,
determinism, and no-network constraints.

## 2026-07-01: Add Local Demo Dataset and End-to-End Daily Brief Demo (Sprint 58)

Decision: add a local example dataset under `examples/daily_brief_demo/` and a
demo script `scripts/run_daily_brief_demo.sh` that runs the complete Atlas Daily
Brief pipeline from structured local inputs.

Rationale: the pipeline (research export → watchlist intelligence → discovery
export → company analysis export → daily summary) was functional but had no
runnable example showing that all five stages connect end-to-end. A minimal demo
dataset (5 knowledge facts, 1 research project, 1 watchlist item — all AMD)
proves the pipeline works locally and gives developers and users a concrete
starting point. No new CLI commands, no new adapters, and no new domains were
needed — only fixture JSON files, a shell script, documentation, and tests. The
demo is explicitly marked as research context, not live market analysis. No
network calls are made at any step.

## 2026-07-01: Remove Daily Shim and Enforce Domain Boundaries (Sprint 75)

Decision: remove `atlas/daily/` (43-line re-export shim), fix the
`atlas/domains/daily_brief/` boundary violation, and extend the domain
boundary test with an explicit legacy-prefix prohibition list.

Changes:
- `atlas/daily/` deleted (2 files, 43 lines — pure re-export, zero logic)
- `atlas/cli/main.py` line 39: `from atlas.daily` → `from atlas.daily_brief`
- `tests/test_daily_brief.py`: import updated from `atlas.daily_brief` directly;
  `LegacyDailyBriefEngine` retained as a local alias for test readability
- `atlas/domains/daily_brief/__init__.py`: rewritten as a namespace stub with
  no imports from legacy modules or capability modules. `DailyBriefOutput`
  re-export (legacy artifact) removed.
- `tests/test_atlas_foundation.py`: stale `DailyBriefOutput` assertion replaced
  with `hasattr(daily_brief, "__all__")` check
- `tests/test_architecture_boundaries.py`: boundary test extended with legacy
  module prefixes; 2 new Sprint 75 tests added (`test_atlas_daily_shim_is_removed`,
  `test_domains_daily_brief_does_not_import_legacy`)
- `docs/LegacyConsolidationPlan.md` and `docs/ArchitectureConsolidation.md`
  updated to mark Sprint 75 as complete

Runtime behavior: unchanged. `atlas daily brief` still works (calls
`atlas.daily_brief` directly). `atlas daily summary` unchanged.
991 tests pass. Demo green. RC verification green.

## 2026-07-01: Legacy Engine Consolidation Plan (Sprint 74)

Decision: create `docs/LegacyConsolidationPlan.md` inventorying all legacy
Atlas modules, mapping their runtime CLI usage, documenting Blueprint-aligned
overlap, confirming provider safety, and selecting a Sprint 75 migration target.

No runtime code was changed. This is a planning-only sprint.

Key findings:
- `atlas/daily/` is a 43-line pure re-export shim. Only `atlas/cli/main.py`
  imports it. Selected as the Sprint 75 removal target (lowest-risk migration).
- `atlas/domains/daily_brief/__init__.py` imports from `atlas.daily_brief`
  (legacy) — a boundary violation. No external code uses this path; resolution
  is scheduled for Sprint 75 alongside shim removal.
- Provider safety confirmed: `atlas/providers/` is never imported by domains,
  capabilities, adapters, demo script, or release verification script.
- 4 legacy module groups identified: thin shims (A), provider-dependent (B),
  self-contained analytics (C), infrastructure/support (D).

Documentation updated:
- `docs/LegacyConsolidationPlan.md` created (new)
- `docs/ArchitectureConsolidation.md` — Sprint 74 section added, boundary
  violation documented
- `README.md` Documentation table — LegacyConsolidationPlan.md link added

## 2026-07-01: README Sprint Notes Archive (Sprint 73)

Decision: move historical sprint notes (Sprints 37–72) from `README.md` into
`docs/SprintHistory.md`. README.md is now a concise 125-line developer guide.

Rationale: `README.md` had grown to 1691 lines — over 93% of which were sprint
notes accumulated during development. The notes are valuable historical context
but not useful to a developer reading the README for the first time. Moving them
to a dedicated document preserves history while making the developer guide
immediately readable.

Changes:
- `README.md` trimmed from 1691 lines to 125 lines
- `docs/SprintHistory.md` created with header + all moved sprint notes
- README Documentation table updated: added `SprintHistory.md` row; fixed
  stale "RC1 release notes" label to "RC1 and RC2 release notes"
- `docs/DecisionLog.md` Sprint 73 entry added

No runtime behavior changed. No code changes. No new capabilities.

## 2026-07-01: Discovery Context Display Name Resolution (Sprint 72)

Decision: add `_resolve_node_display_name` in `atlas/capabilities/daily_brief/engine.py`
and use it in `_discovery_section` instead of `candidate.identifier`.

Rationale: the Discovery Context previously displayed raw knowledge node IDs
(`company-amd`, `company-nvda`) which are internal technical identifiers. The
discovery engine already computed human-readable `title` fields via
`_title_from_identifier` (`company-amd` → `AMD`), but the Daily Brief renderer
ignored them. This sprint wires the two together without changing any model or
export format.

Resolution order (deterministic, explicit, no fuzzy/AI):
1. `candidate.title` if non-empty
2. `candidate.ticker` if non-empty
3. `company-{x}` → `X.upper()` (single-segment suffix only)
4. original identifier as safe fallback

One pre-existing test (`test_discovery_candidate_identifier_used_as_item_title`)
asserted the old buggy behavior and was renamed and corrected. 17 new tests
added in `tests/test_discovery_display_names.py`.

Demo output change: Discovery Context now shows `AMD` and `NVDA` instead of
`company-amd` and `company-nvda`.

## 2026-07-01: RC2 Release Verification (Sprint 71)

Decision: declare Atlas Internal Release Candidate 2 (v0.1.0-rc2), extending
the RC1 documentation in `docs/ReleaseCandidate.md` with a new RC2 section.
No new product capability was added.

Verification results:
- 947 tests pass (0 failures)
- `scripts/verify_release_candidate.sh` — all 7 steps green
- `scripts/run_daily_brief_demo.sh` — all 7 steps complete
- All five Daily Brief input surfaces exercised in demo
- No false "No knowledge facts are linked" in output
- No forbidden language in output
- No network calls

Documentation updated:
- `docs/ReleaseCandidate.md` — RC2 section prepended; RC1 preserved below
- `README.md` — version updated to RC2; test count updated to 947; capabilities table updated
- `scripts/verify_release_candidate.sh` — final echo updated from "RC1" to "RC2"
- `docs/ArchitectureConsolidation.md` — noted RC2 review; no structural changes
- `docs/DecisionLog.md` — Sprint 71 entry added

## 2026-07-01: Evidence Link Resolution — Knowledge Facts via Company Node ID (Sprint 70)

Decision: add `--knowledge` flag to `atlas watchlist intelligence` and a
`assign_knowledge_facts` function in `atlas/adapters/watchlist.py` that
distributes knowledge facts to watchlist items by ticker or by the explicit
`company-{ticker.lower()}` node ID pattern (e.g. `company-amd` → `AMD`).
Update demo script Step 2 to pass `--knowledge examples/daily_brief_demo/knowledge.json`.

Rationale: knowledge facts in `knowledge.json` use `subject_node_id` values
like `"company-amd"` and `"company-nvda"`, while watchlist items identify
companies by ticker (`"AMD"`, `"NVDA"`). Without a mapping, `WatchlistItem.knowledge_facts`
was always empty, triggering `WatchlistUnknown("No Supporting Knowledge Facts",
"No knowledge facts are linked.", ticker)` which propagated as
`"AMD: No knowledge facts are linked."` into `suggested_next_research_steps` and
ultimately into the Daily Brief's "Suggested Next Research Steps" section.

Matching strategy: deterministic explicit mapping only. A fact matches a
watchlist item when `fact.subject_node_id == ticker` (exact) OR
`fact.subject_node_id == f"company-{ticker.lower()}"`. No fuzzy matching.
The `_node_id_matches_ticker` helper in `atlas/adapters/watchlist.py` is the
single, documented, tested implementation of this rule.

Demo output change: "Suggested Next Research Steps" no longer contains
`"AMD: No knowledge facts are linked."` / `"NVDA: No knowledge facts are linked."`.
Steps now reflect actual watchlist research priorities.

`examples/daily_brief_demo/README.md` Pipeline Steps updated to include
`--knowledge` in Step 2. Expected output updated to match new steps.

## 2026-07-01: Portfolio Demo Integration (Sprint 69)

Decision: add `examples/daily_brief_demo/portfolio.json` and pass `--portfolio`
to `atlas daily summary` in the demo script, completing all five Daily Brief
input surfaces in the demo.

Portfolio file: NVDA 55%, AMD 30%, Cash 15% — static example data, no live
prices, no investment advice. Concentration at 55% triggers `ConcentrationLevel.HIGH`
(threshold ≥ 35%), exercising the HIGH priority path in "What Deserves Attention".

Demo output changes from Sprint 68:
- Opening Summary: overall priority is now `high` (was `moderate`)
- Included Context: now includes `Portfolio: available`
- What Deserves Attention: `[!] Portfolio concentration: Concentration appears
  high. This deserves review.` added
- Portfolio Context section: now present (Holdings: 3, Concentration: High,
  55.0% largest, Cash: 15.0%)
- What Can Safely Wait: portfolio LOW items (holdings count, cash weight) added

`scripts/verify_release_candidate.sh` updated to also check "Portfolio Context"
section presence. All 7 verification steps still green.

12 new tests added to `tests/test_daily_brief_demo.py` (Sprint 69 section).
932 tests pass total (920 prior + 12 new).

## 2026-07-01: Post-RC Smoke Test and Release Verification (Sprint 68)

Decision: verify Atlas Internal RC1 (`atlas-v0.8-internal-rc1`) from a
clean-user perspective and add a release verification script.

Verification results:
- `git tag` confirms `atlas-v0.8-internal-rc1` exists on `main` at `178b27f`
- Compile check: clean
- Full test suite: 910 passed, 0 failed
- Demo: all 7 steps completed; all 7 output files present
- Output sections: Opening Summary, Included Context, What Deserves Attention,
  Company Analysis Context, What Can Safely Wait, Research Framing — all present
- Forbidden language: none found in `daily_brief.txt`
- Cleanup: `rm -rf tmp/atlas_demo` removes all generated files cleanly

Fix: `docs/ReleaseCandidate.md` stated 883 tests (written at Sprint 67 start
before 27 new release tests were counted). Corrected to 910.

Addition: `scripts/verify_release_candidate.sh` — 7-step local verification
script (compile, test, demo, file check, section check, language check,
cleanup). Runs end-to-end in ~20s. No network calls. Self-cleaning.

10 new tests added to `tests/test_release_candidate.py` verifying the
verification script exists and meets all constraints.

920 tests pass total (910 prior + 10 new).

## 2026-07-01: First Internal Release Candidate (Sprint 67)

Decision: declare Atlas v0.1.0-rc1 as the first internal release candidate
(RC1), completing the foundation sprint series (Sprints 36–67).

Deliverables:
- `docs/ReleaseCandidate.md` — RC1 release notes covering: what works, how to
  run tests and the demo, architecture state, release checklist, known
  limitations, technical debt, and next phase recommendation.
- `README.md` — replaced sprint-by-sprint top section with a clean developer
  guide (What Atlas Is, What Atlas Is Not, Current Capabilities table,
  Install, Run Tests, Quickstart, Architecture State, Documentation table,
  Constraints). Sprint notes preserved below a clear "Historical Sprint Notes"
  separator. Duplicate "Install locally" / "Quickstart" sections at the
  bottom cleaned up.
- `docs/ArchitectureConsolidation.md` — updated sprint reference to RC1.
- `tests/test_release_candidate.py` — 27 lightweight static tests verifying
  RC1 document existence, content, no-recommendation-language, and README
  developer-guide sections.

Rationale: after 67 sprints the repository had a clear working pipeline but
no single place that described the current state for a new developer. The
README top section read as a sprint log rather than a project guide. RC1 fixes
this by creating a stable documentation baseline before the next phase begins.

910 tests pass total (883 prior + 27 new).

## 2026-07-01: Local Demo UX Polish and First User Guide (Sprint 66)

Decision: improve the local Daily Brief demo experience and create a clear
user/developer guide for running Atlas locally.

Changes:
- `scripts/run_daily_brief_demo.sh` — added venv auto-detection (`ATLAS=`
  variable resolves `.venv/bin/atlas` or PATH-available `atlas`), added a
  clear error message when neither is found, added blank lines between steps
  for readability, saved Daily Brief output to `tmp/atlas_demo/daily_brief.txt`
  via `tee`, and added a generated-files summary at the end.
- `examples/daily_brief_demo/README.md` — rewritten to include: Purpose,
  What This Is Not, Prerequisites, Quickstart, Input Files table, Generated
  Files table with step mapping, Pipeline Steps (manual commands), Expected
  Output excerpt (accurate to actual demo output including "What Can Safely
  Wait" and "Discovery Context"), Clean Up, Known Limitations, and
  Architecture Notes sections.
- `README.md` — added "Quickstart: Run the Daily Brief Demo" section with
  one-line install, one-line run, cleanup command, and link to full guide.
- `tests/test_daily_brief_demo.py` — added 20 Sprint 66 asset verification
  tests covering: script existence, no network tools, no python one-liners,
  `set -euo pipefail`, output file, cleanup instructions, error handling,
  README content (disclaimers, sections, forbidden language), and root README
  Quickstart.

Rationale: the demo script failed with `atlas: command not found` for
developers who had not activated the virtualenv. The demo documentation
described an outdated expected output (missing "What Can Safely Wait" and
"Discovery Context" sections added in Sprints 64–65). The root README had
no clear path for a developer to run Atlas locally.

881 tests pass total (861 prior + 20 new).

## 2026-07-01: Daily Brief Priority Routing — HIGH/MODERATE Only in What Deserves Attention (Sprint 65)

Decision: remove LOW priority items from `_opening_section` ("What Deserves Attention")
and route them to the appropriate lower-signal destinations.

Two LOW items were removed from "What Deserves Attention":
1. **Knowledge context** — moved to "Included Context" via `_render_included_context`,
   which now reads `report.knowledge_node_count` (new field on `DailyBriefReport`).
2. **Company analysis with no unknowns** — excluded from `_opening_section` entirely;
   remains visible in "Company Analysis Context" and collected into "What Can Safely Wait"
   by the existing `_collect_safely_wait_items` mechanism from Sprint 64.

The fallback item in "What Deserves Attention" was updated to distinguish two states:
- **No inputs at all** → original "No meaningful developments were identified" message.
- **Inputs exist but all are LOW priority** → new calm message: "Context has been organised.
  No items require immediate attention." Determined by `_has_meaningful_input(data)`.

`DailyBriefReport` gained `knowledge_node_count: int = 0` (optional field with default,
no breaking change). The renderer reads it to populate "Included Context".

Rationale: "What Deserves Attention" was losing signal by promoting LOW items into the
same section as HIGH/MODERATE items. Readers had to scan all items to find what truly
needed attention. After this sprint, every item in "What Deserves Attention" is
actionable-research-worthy. LOW items remain visible in context-appropriate sections.

4 pre-existing tests updated to reflect the new routing. 16 new tests added in
`tests/test_daily_brief_priority_routing.py`. 861 tests pass total.

## 2026-07-01: Daily Brief What Can Safely Wait Section (Sprint 64)

Decision: add a "What Can Safely Wait" section to `render_daily_brief_report`
in `atlas/capabilities/daily_brief/engine.py`, populated by a new private
helper `_collect_safely_wait_items`.

The helper scans all sections except "What Deserves Attention" (the opening
summary) for LOW priority items and returns them in section order. The
renderer appends the section after "Suggested Next Research Steps" and before
"Research Framing" when the collected list is non-empty. No model changes
were required — LOW priority items already existed in the report structure.

Rationale: LOW priority items appeared throughout detail sections with no
visual distinction from MODERATE items (both rendered without a priority
marker). Readers had no consolidated view of what could be deferred. The new
section collects these items in one place so readers can quickly identify
what does not require immediate research attention. "LOW priority" means
"can be reviewed later," not "unimportant."

Sources collected: Portfolio Context (holdings, low concentration, cash weight),
Company Analysis Context (companies with no unknowns), Watchlist Context
(suggested research steps). "What Deserves Attention" is excluded to avoid
duplicating the aggregate summary items it contains.

The section is omitted when no inputs are supplied, when all company reports
have unknowns (MODERATE), or when no LOW items exist in any detail section.

22 new tests added in `tests/test_daily_brief_safely_wait.py`. All 823
pre-existing tests continue to pass (845 total).

## 2026-07-01: Daily Brief Opening Summary Alignment (Sprint 63)

Decision: add `_company_analysis_opening_item` helper and call it from
`_opening_section` so company analysis reports always generate an item in
the "What Deserves Attention" section.

Rationale: before Sprint 63, "What Deserves Attention" displayed the
"Status: No meaningful developments" fallback even when company analysis
reports were present — contradicting the Opening Summary which correctly
stated those reports were available. The fix is targeted: a new private
helper inspects `data.company_reports`, counts companies with unknowns,
and returns a `DailyBriefItem` with `moderate` priority if any company has
unknowns, or `low` if all are clean. No model changes. No new CLI flags.
No external calls. The fallback "no developments" item is now suppressed
whenever company reports exist.

Priority mapping:
- Any company with unknowns → `moderate` ("includes observations that deserve review")
- All companies clean → `low` ("context is available for review")

27 new tests added in `tests/test_daily_brief_opening_summary.py`. All
796 pre-existing tests continue to pass (823 total).

## 2026-07-01: Daily Brief Output Readability Improvements (Sprint 62)

Decision: rewrite `render_daily_brief_report` in
`atlas/capabilities/daily_brief/engine.py` for improved terminal readability,
and reorder `_build_sections` to surface Company Analysis before Research and
Watchlist.

Changes:
- Separator lines (`─ × 45`) between all major sections.
- "Included Context" block after Opening Summary: lists which companies,
  research projects, watchlist, discovery, and portfolio data are present.
  Omitted when no inputs are supplied.
- Company Analysis Context renders each company as a named group (ticker as
  sub-header, detail indented) rather than a flat list of items.
- Priority markers: `[!]` for high, `[·]` for moderate, no marker for low.
  Removes the noisy `[low]` / `[moderate]` / `[high]` bracket labels.
- Evidence Gaps section now appears before Unresolved Questions (was after).
- Unresolved Questions grouped by company ticker when context is set.
- Section order: Company Analysis Context now appears before Research Context
  and Watchlist Context (was last among detail sections).

Rationale: the previous output was structurally flat, printed debug-style
priority labels, and buried company analysis at the bottom. The new format
makes it immediately clear which companies are included, what deserves
attention, and how unknowns map to each company — without adding features,
AI, or network calls. All changes are in the renderer and section ordering;
the report model and CLI interface are unchanged.

25 new tests added in `tests/test_daily_brief_output_readability.py`. All
771 pre-existing tests continue to pass (796 total).

## 2026-07-01: Fix Evidence Gap Resolver — Gaps from Unknowns, Not Evidence Links (Sprint 61)

Decision: rewrite `_build_evidence_gaps` in `atlas/capabilities/daily_brief/engine.py`
to surface only company analysis `unknowns` whose title contains "evidence" (e.g.
"Missing Evidence"), not `evidence_links`.

Rationale: `evidence_links` on a `CompanyAnalysisReport` represent knowledge
facts the engine *confirmed* as supporting evidence — they are linked, not gaps.
The old implementation iterated `evidence_links` and displayed each as a gap,
which was semantically backwards: confirmed evidence was reported as missing
evidence. The fix scopes gaps per company (AMD gaps cannot appear as NVDA gaps)
and filters by unknown title so metadata unknowns ("Missing Sector", "Missing
Country") are excluded. When all metadata and knowledge facts are supplied, the
Evidence Gaps section no longer appears in the daily brief — which is the correct
outcome. A new `_is_evidence_gap_unknown(title)` helper makes the classification
rule explicit and testable. 17 new unit tests added in
`tests/test_evidence_gap_resolver.py`. Two pre-existing tests that asserted the
buggy behavior were renamed and rewritten to assert correct behavior.

## 2026-07-01: Add --sector and --country to Company Analysis Export (Sprint 57)

Decision: add two optional string flags — `--sector` and `--country` — to
`atlas company-analysis export`. Both populate `Company` fields used by
`CompanyAnalysisEngine` without requiring any network calls or new adapters.

Rationale: Sprint 56 left `Company.sector` and `Company.country` always empty,
causing "Missing Sector" and "Missing Country" unknowns to appear in every
engine-backed export. Both fields accept user-supplied local strings, require no
external lookup, and follow the pattern established in Sprint 56 for optional
metadata flags. When all four metadata flags (`--company-name`, `--sector`,
`--country`, `--business-description`) are supplied alongside `--ticker`, all
core "Missing X" unknowns are eliminated and engine confidence improves to
`moderate`. Only "Missing Evidence" remains when no knowledge facts are
provided. Both flags are entirely optional — omitting them preserves Sprint 56
behavior exactly. No new files were added; only `atlas/cli/main.py` was modified.

## 2026-07-01: Deprecate `atlas daily brief` Command (Sprint 76)

Decision: deprecate `atlas daily brief` in favor of `atlas daily summary`
(Blueprint-aligned). The command now prints a deprecation message and exits
without calling the legacy `DailyBriefEngine` or any provider.

Rationale: Sprint 75 removed the `atlas/daily/` shim. The next natural step is
to eliminate the remaining consumer of `atlas/daily_brief/` (the legacy
provider-coupled engine). Option A (deprecate the command) is smaller and
lower-risk than Option B (wire the command through the new capability). It
reduces provider coupling without changing the Blueprint-aligned path.
`atlas/daily_brief/` remains on disk to allow comparison and confirm no
external consumers exist before deletion in Sprint 77 or later.

## 2026-07-01: Remove Legacy `atlas/daily_brief/` Engine (Sprint 77)

Decision: delete `atlas/daily_brief/` (2 files, 353 lines) after confirming
no active imports remain. Six legacy engine unit tests were removed; one CLI
deprecation test was retained. Three architecture guardrail tests were added.

Rationale: Sprint 76 deprecated `atlas daily brief` and removed the CLI import.
The engine itself had no remaining consumers. Deletion reduces the legacy surface
area and eliminates the last provider-coupled code called by any Daily Brief path.
The guardrail tests ensure the module cannot be silently reintroduced.

## 2026-07-01: Deprecate `atlas watchlist analyze` Command (Sprint 78)

Decision: deprecate `atlas watchlist analyze` in favor of `atlas watchlist
intelligence` (Blueprint-aligned). The command now prints a deprecation message
and exits without calling `WatchlistEngine` or any provider.

Rationale: Follows the two-step pattern from Sprints 76–77. Unlike the daily
brief path (where DailyBriefEngine had only one CLI consumer), WatchlistEngine
is used by 5 other legacy engines. The CLI deprecation is safe and immediate;
full WatchlistEngine deletion requires retiring those 5 dependent engines first,
which is a larger multi-sprint effort outside Sprint 78's scope.

## 2026-07-01: Deprecate `atlas portfolio analyze` Command (Sprint 79)

Decision: deprecate `atlas portfolio analyze` in favor of `atlas portfolio
summary` (Blueprint-aligned, no providers). The command now prints a
deprecation message and exits without calling `PortfolioIntelligenceEngine`
or any provider.

Rationale: Follows the two-step pattern from Sprints 76–78. `atlas portfolio
summary` already exists as the Blueprint-aligned replacement. `atlas portfolio
review` is left unchanged in this sprint — it is a separate legacy path with
its own review engine and will be addressed in Sprint 80 or later.

## 2026-07-01: Deprecate `atlas portfolio review` Command (Sprint 80)

Decision: deprecate `atlas portfolio review` in favor of `atlas portfolio
summary` (Blueprint-aligned, no providers). The command now prints a
deprecation message and exits without calling `PortfolioReviewEngine` or
any provider.

Rationale: Follows the two-step pattern from Sprints 76–79. `atlas portfolio
summary` already exists as the Blueprint-aligned replacement. After Sprint 80,
both `atlas portfolio analyze` (Sprint 79) and `atlas portfolio review` (Sprint
80) are deprecated. `atlas portfolio summary` is the sole active portfolio
command. `PortfolioReviewEngine` remains on disk — it is still referenced by
`AtlasHomeEngine` (Group B) and cannot be deleted without broader consolidation.

## 2026-07-01: Deprecate `atlas evidence assess` Command (Sprint 81)

Decision: deprecate `atlas evidence assess`. No Blueprint-aligned evidence
capability exists yet, so the deprecation message directs users toward future
Blueprint-aligned decision and research capabilities rather than inventing a
specific replacement command.

Rationale: Group C self-contained module. `EvidenceQualityEngine` makes no
provider or network calls, making the CLI deprecation safe and immediate.
The engine itself cannot be deleted yet — it is used by `decision_journal`,
`comparison`, and `watchlist_review` legacy engines. CLI surface area is
reduced; full engine retirement requires broader consolidation.

## 2026-07-01: Deprecate `atlas reason analyze` Command (Sprint 82)

Decision: deprecate `atlas reason analyze`. No Blueprint-aligned reasoning
command exists yet, so the deprecation message directs users toward future
Blueprint-aligned decision and research capabilities rather than inventing
a specific replacement command.

Rationale: Group C self-contained module. `atlas.reasoning.ReasoningEngine`
makes no provider or network calls, making the CLI deprecation safe.
The `_build_reasoning_report` helper was removed as dead code after the
command body was replaced. The engine itself cannot be deleted yet — it is
still lazily imported by `atlas/principles/engine.py`.

Note: `atlas/domains/decision/engine.py` defines a separate `ReasoningEngine`
class (Blueprint-aligned protocol) — this is distinct from the legacy
`atlas.reasoning.ReasoningEngine` and is unaffected by this sprint.

---

## Sprint 83 — 2026-07-01: Deprecate `atlas risk size`

**Decision:** Deprecate `atlas risk size` CLI command (stub, exit 0) rather
than deleting it immediately.

**Rationale:** Same safe two-step pattern as Sprints 76–82. The `atlas/risk/`
engine is self-contained (Group C) and has no provider dependencies in the CLI
path. However, `RiskAnalysis` (a data type) is still imported by
`atlas/intelligence/`, `atlas/reasoning/`, and `atlas/conversation/` engines.
`RiskEngine` itself has no remaining non-CLI callers — but engine deletion
belongs to a future sprint after those consumers are confirmed removable.

**Alternatives considered:**
- Immediate deletion: too broad; `RiskAnalysis` type still in use elsewhere.
- Immediate migration: no Blueprint-aligned risk-sizing capability exists yet;
  inventing a replacement command would be premature.

**Outcome:** 16 new Sprint 83 deprecation tests; 1068 tests passing.

---

## Sprint 84 — 2026-07-01: Centralized Deprecation Registry

**Decision:** Create `atlas/cli/deprecations.py` as a CLI-local deprecated command
registry. Route all 7 deprecated command bodies through `deprecated_command_message()`.

**Rationale:** Sprints 76–83 each inlined a deprecation message string directly in
the CLI command body. This created 7 copies of near-identical boilerplate with no
single source of truth for message wording, replacement commands, or removal criteria.
The registry consolidates this without changing user-facing behavior.

**Design constraints applied:**
- Registry is CLI-local (no engine, provider, or domain imports)
- No framework dependency — pure Python dataclass + dict
- `DeprecatedCommand` is frozen and deterministic
- User-facing messages are preserved exactly

**Alternatives considered:**
- Leave inline (rejected: no single source of truth, hard to audit retirement readiness)
- Move to domains layer (rejected: deprecation is a CLI concern, not a domain concern)
- Add dynamic lookup at runtime (rejected: over-engineered for a static list of 7 items)

**Outcome:** 46 new registry tests; 1114 tests passing. Architecture boundaries clean.
Recommended Sprint 85: retire `atlas daily brief` command body (engine already deleted).

---

## Sprint 85 — 2026-07-01: Retire `atlas daily brief` Command Body

**Decision:** Remove the `atlas daily brief` command body and registration from
`atlas/cli/main.py`. Move its registry entry to `_RETIRED_REGISTRY`.

**Rationale:** The underlying `atlas.daily_brief` engine was deleted in Sprint 77.
Sprint 76 deprecated the CLI stub, and Sprint 84 centralized its message into the
registry. By Sprint 85 the stub was a pure no-op with no engine dependency, no
provider calls, and no active callers. Removing it is zero-risk and reduces CLI
surface area by one command.

**Alternatives considered:**
- Leave as deprecated stub indefinitely: rejected — the engine is gone, the stub
  serves no purpose, and it clutters the CLI help output.
- Add a compatibility alias: rejected — `atlas daily summary` provides complete
  replacement; a shim would only perpetuate legacy surface area.

**Outcome:** `atlas daily brief` is no longer callable. `atlas daily summary` is
the sole Daily Brief entry point. 1111 tests passing. `_RETIRED_REGISTRY` pattern
established for future retirements.

---

## Sprint 86 — 2026-07-01: Retire `atlas evidence assess` Command Body; Retain Engine

**Decision:** Remove `atlas evidence assess` command body. Retain `atlas/evidence/`
engine (`EvidenceQualityEngine`) on disk.

**Rationale:** The CLI stub was a pure no-op with no engine calls. Removing it is
zero-risk and reduces CLI surface area. However, the engine itself cannot be deleted:
three active non-deprecated legacy engines instantiate `EvidenceQualityEngine` —
`atlas/comparison/`, `atlas/decision_journal/`, and `atlas/watchlist_review/`. Deleting
the engine would break all three.

**Finding from sprint:** The Sprint 81 doc comment ("self-contained Group C module,
no known dependents") was incorrect — the engine has three callers that were not
identified at deprecation time. Tests now explicitly assert caller presence as an
invariant, so future sprints cannot accidentally delete the engine without updating them.

**Alternatives considered:**
- Delete engine despite active callers: rejected — would break comparison, decision
  journal, and watchlist review functionality.
- Defer command retirement until engine can be deleted: rejected — command and engine
  deletion are independent; retiring the stub costs nothing and reduces surface area.

**Outcome:** Command retired. Engine stays. 1107 tests passing. `_RETIRED_REGISTRY`
now has 2 entries (daily brief, evidence assess).

---

## Sprint 87 — 2026-07-01: Retire `atlas reason analyze` Command Body; Retain Engine

**Decision:** Remove `atlas reason analyze` command body. Retain `atlas/reasoning/`
engine on disk.

**Rationale:** The CLI stub was a pure no-op — safe to remove regardless of engine
state. The underlying `atlas.reasoning.ReasoningEngine` cannot be deleted yet because
`atlas/principles/engine.py` contains a lazy import of `render_reasoning_report`
inside `check_reasoning_report()`.

**Key finding from sprint:** `check_reasoning_report()` has no external callers —
it is exported by `atlas/principles/__init__.py` but nothing calls it. The lazy
import therefore never fires at runtime. This means the `atlas.reasoning` runtime
dependency is weaker than previously documented, but the import statement still
exists and engine deletion still requires removing it explicitly.

**TYPE_CHECKING import note:** `atlas/principles/engine.py` also imports `ReasoningReport`
under `if TYPE_CHECKING:` — this is not a runtime dependency and does not block deletion.

**Blueprint-aligned ReasoningEngine note:** `atlas/domains/decision/engine.py` defines
its own `ReasoningEngine` protocol class — completely separate from the legacy
`atlas.reasoning.ReasoningEngine`. Not affected by this sprint.

**Outcome:** Command retired. Engine stays. 1104 tests passing. `_RETIRED_REGISTRY`
now has 3 entries (daily brief, evidence assess, reason analyze).

---

## Sprint 88 — 2026-07-01: Retire `atlas risk size` Command Body; Retain Engine

**Decision:** Remove `atlas risk size` command body. Retain `atlas/risk/` module.

**Rationale:** The CLI stub was a pure no-op — safe to remove. The underlying
`RiskEngine` has no production instantiation points outside the deprecated command.
However, `RiskAnalysis` (a data type in the same file) is still actively imported
by `atlas/conversation/`, `atlas/intelligence/`, and `atlas/reasoning/`. Deleting
`atlas/risk/engine.py` would break those three imports. Separating `RiskEngine` from
`RiskAnalysis` in the same file is possible but constitutes surgical refactoring that
belongs in its own sprint rather than alongside a command retirement.

**Sprint spec rule applied:** "If RiskEngine and RiskAnalysis live in the same file
and separating them would create migration risk, do not delete the engine in this
sprint." — applied exactly as specified.

**Outcome:** Command retired. Engine stays. 1101 tests passing. `_RETIRED_REGISTRY`
now has 4 entries (daily brief, evidence assess, reason analyze, risk size).
Active deprecated `_REGISTRY` now has 3 entries (watchlist analyze, portfolio analyze,
portfolio review).

## Sprint 89 — 2026-07-02: Retire `atlas portfolio analyze` Command Body; Retain Engine

**Decision:** Remove `atlas portfolio analyze` command body. Retain `atlas/analysis/portfolio` module.

**Rationale:** The CLI stub was a pure no-op — safe to remove. The underlying
`PortfolioIntelligenceEngine` (and the shared types `Portfolio` and `PortfolioAnalysis`)
are still actively imported by 10+ modules across the codebase: `atlas/intelligence`,
`atlas/conversation`, `atlas/decision`, `atlas/dashboard`, `atlas/reasoning`, `atlas/home`,
`atlas/suitability`, `atlas/risk_drift`, `atlas/monitoring`, and `atlas/portfolio_review`.
Deleting the engine would break all those imports. Engine deletion deferred until all
callers are retired.

**Sprint 89 did not retire `atlas portfolio review`** — it remains an active deprecated
command (stub only). Retiring it was left for Sprint 90 to avoid scope creep and to allow
a focused import audit of `PortfolioReviewEngine`.

**Outcome:** Command retired. Engine stays. 1106 tests passing. `_RETIRED_REGISTRY`
now has 5 entries (daily brief, evidence assess, reason analyze, risk size, portfolio analyze).
Active deprecated `_REGISTRY` now has 2 entries (watchlist analyze, portfolio review).

## Sprint 90 — 2026-07-02: Retire `atlas portfolio review` Command Body; Retain Engine

**Decision:** Remove `atlas portfolio review` command body. Retain `atlas.portfolio_review` module.

**Rationale:** The CLI stub was a pure no-op — safe to remove. The import audit revealed
one active non-deprecated production caller: `atlas/home/engine.py` (`AtlasHomeEngine`)
imports `PortfolioReviewEngine` and `PortfolioReviewInput` from `atlas.portfolio_review`
and instantiates `PortfolioReviewEngine()` at runtime. Engine deletion was therefore
blocked — this is the same pattern used in Sprints 86–89.

**Important naming note:** `atlas.domains.portfolio.review` defines its own
`PortfolioReviewEngine` (Blueprint-aligned). This is a completely separate class from
the legacy `atlas.portfolio_review.PortfolioReviewEngine`. The Blueprint version is
unaffected by this sprint. The legacy version remains on disk for `AtlasHomeEngine`.

**Engine deletion path:** Retire or migrate `AtlasHomeEngine` to use the Blueprint-aligned
`atlas.domains.portfolio.review.PortfolioReviewEngine` instead of the legacy one.
Once that migration is complete, `atlas.portfolio_review` can be deleted.

**Outcome:** Command retired. Engine stays. 1111 tests passing. `_RETIRED_REGISTRY`
now has 6 entries (daily brief, evidence assess, reason analyze, risk size, portfolio analyze,
portfolio review). Active deprecated `_REGISTRY` now has 1 entry (watchlist analyze).

## Sprint 91 — 2026-07-02: Retire `atlas watchlist analyze` Command Body; Retain Engine

**Decision:** Remove `atlas watchlist analyze` command body. Retain `atlas.analysis.watchlist` module.

**Rationale:** The CLI stub was a pure no-op — safe to remove independently of engine deletion.
The import audit confirmed five active non-deprecated production callers of `WatchlistEngine`:
`atlas/intelligence`, `atlas/decision`, `atlas/monitoring`, `atlas/watchlist_review`, and
`atlas/conversation`. Engine deletion requires retiring all five callers — a multi-sprint
effort deferred to Sprint 92+.

**Sprint 91 completes the CLI deprecated command retirement plan.** All seven originally
deprecated CLI commands (daily brief, evidence assess, reason analyze, risk size, portfolio
analyze, portfolio review, watchlist analyze) have now had their command bodies retired.
The active `_REGISTRY` is empty. `atlas/cli/deprecations.py` is retained for retired-command
history and audit purposes.

**Outcome:** Command retired. Engine stays. 1116 tests passing (3 skipped — parametrized
tests with empty EXPECTED_COMMANDS, by design). `_RETIRED_REGISTRY` now has 7 entries.
Active `_REGISTRY` is empty.

## Sprint 92 — 2026-07-02: WatchlistEngine Caller Audit; Redundant Double-Run Eliminated

**Decision:** Audit `atlas/monitoring/` and `atlas/watchlist_review/` as WatchlistEngine caller
targets. Both are active CLI-backed modules — neither can be retired this sprint. Eliminate the
redundant double WatchlistEngine invocation found in `WatchlistReviewEngine.review()`. Add an
exclusivity guardrail test on the WatchlistEngine caller set.

**Rationale:** Both `atlas/monitoring/` and `atlas/watchlist_review/` power active CLI commands
(`atlas monitor watchlist` and `atlas watchlist review` respectively). Retirement is blocked.
However, the audit revealed `WatchlistReviewEngine.review()` was calling `WatchlistEngine.analyze()`
twice on the same inputs per review — once directly, once again inside
`MonitoringEngine.snapshot_watchlist()`. Extracting `snapshot_watchlist_from_analysis()` from
`MonitoringEngine` and updating `review()` to use it eliminates the redundant run without changing
behavior. Sharing the `WatchlistEngine` instance between `WatchlistReviewEngine` and its internal
`MonitoringEngine` reduces object count from 2 to 1.

Adding the caller exclusivity guardrail (`test_watchlist_engine_callers_are_exactly_the_known_set`)
prevents new WatchlistEngine callers from being added unnoticed during future sprints.

**Outcome:** WatchlistEngine caller count unchanged at 5. Redundant double-run eliminated.
One shared WatchlistEngine instance in WatchlistReviewEngine. Exclusivity guardrail added.
1118 tests passing (3 skipped). Demo passed. Release verification green.

## Sprint 93 — 2026-07-02: Remove WatchlistEngine from Monitoring Runtime Path

**Decision:** Replace `atlas monitor watchlist` CLI path with Blueprint-aligned `WatchlistIntelligenceEngine`,
removing `WatchlistEngine` from `atlas/monitoring/engine.py`. Retain `snapshot_watchlist_from_analysis()`
in `MonitoringEngine` for `watchlist_review`'s use.

**Rationale:** Sprint 92 isolated the watchlist monitoring path behind `snapshot_watchlist_from_analysis`.
Sprint 93's goal was to remove `WatchlistEngine` from monitoring entirely. The Blueprint-aligned
`WatchlistIntelligenceEngine` accepts `WatchlistIntelligenceInput` (name + minimal ticker items)
and produces research-coverage signals (items needing attention, evidence gaps, open questions)
rather than company scores. This is a valid replacement because:
- `atlas monitor watchlist` is about tracking research coverage gaps, not scoring companies
- The new signals are deterministic, local-only, provider-free
- No recommendation language; no buy/sell language
- The architecture boundary permits legacy modules to import capabilities (only domains are forbidden)

`snapshot_watchlist_from_analysis(analysis: WatchlistAnalysis)` is retained in `MonitoringEngine`
because `atlas/watchlist_review/engine.py` still calls it after computing its own `WatchlistAnalysis`
via its direct `WatchlistEngine`. That dependency is the Sprint 94 target.

**Output change:** `atlas monitor watchlist` signals changed from company-score-based (atlas_score,
valuation.score, quality.score) to research-coverage-based (items needing attention, evidence gaps,
open questions). Behavior intent preserved (monitoring research coverage health). Documented.

**Outcome:** WatchlistEngine caller count reduced 5 → **4** (intelligence, decision, watchlist_review,
conversation). `atlas/monitoring/engine.py` no longer imports `WatchlistEngine`. Provider parameter
made optional in `monitor_watchlist`/`snapshot_watchlist` — CLI call unchanged. 1121 tests passing
(3 skipped). Demo passed. Release verification green.

## Sprint 94 — 2026-07-02: Remove WatchlistEngine from Watchlist Review

**Decision:** Replace `atlas/watchlist_review/engine.py` direct `WatchlistEngine` usage with the
Blueprint-aligned `MonitoringEngine.snapshot_watchlist()` (introduced Sprint 93). Remove
`snapshot_watchlist_from_analysis()` from `MonitoringEngine` once it has no runtime callers.

**Rationale:** `WatchlistReviewEngine.review()` used `WatchlistEngine.analyze()` to produce a
`WatchlistAnalysis` for two purposes: (1) as input to `snapshot_watchlist_from_analysis()` for the
monitoring snapshot, and (2) to supply `atlas_score` and `confidence` per ticker to `_review_items`.
Sprint 93 made `MonitoringEngine.snapshot_watchlist(watchlist)` Blueprint-aligned — so purpose (1)
can be replaced with a direct call to that method (no legacy analysis needed as intermediate).
Purpose (2) (per-ticker `atlas_score`) cannot be replaced without WatchlistEngine or a provider call,
so `_review_items` now defaults to `base_score=45` for all companies. This is a documented, acceptable
behavior change: `relevance_score` values become less differentiated but remain deterministic and
local-only. With `snapshot_watchlist_from_analysis` now having no runtime callers, the bridge method
is deleted from `MonitoringEngine`, and `WatchlistAnalysis` is dropped from its imports.

**Outcome:** WatchlistEngine caller count reduced 4 → **3** (intelligence, decision, conversation).
`atlas/watchlist_review/engine.py` and `atlas/monitoring/engine.py` both no longer import
`WatchlistEngine`. `snapshot_watchlist_from_analysis` removed. 1121 tests passing (3 skipped).
Demo passed. Release verification green.

---

**Sprint 95 (2026-07-02): Remove WatchlistEngine from `atlas/decision/decision_engine.py`**

**Decision:** Replace `AtlasDecisionEngine` direct `WatchlistEngine` usage with `WatchlistIntelligenceEngine` (Blueprint capability), following the Sprint 93/94 pattern.

**Rationale:**
- `atlas/decision/` was the smallest remaining WatchlistEngine caller — clear migration path.
- `DecisionResult.watchlist_intelligence` now carries richer research signals (`WatchlistIntelligenceReport`) rather than legacy scoring output (`WatchlistAnalysis`).
- Consistent with Blueprint principle: decision layer should consume capability-level intelligence, not raw legacy engine scores.
- Confidence bonus (+4 for watchlist context) preserved unchanged — only the underlying source changes.

**Alternatives considered:**
- Keep `WatchlistAnalysis` in `DecisionResult` and only remove `WatchlistEngine` from the engine: rejected — would leave a dead import of `WatchlistAnalysis` in the result model.
- Migrate `atlas/conversation/` first: deferred — conversation has more surface area; decision was lower risk.

**Outcome:** WatchlistEngine caller count reduced 3 → **2** (intelligence, conversation).
`atlas/decision/decision_engine.py` no longer imports `WatchlistEngine`. `DecisionResult.watchlist_intelligence` holds `WatchlistIntelligenceReport | None`. 1122 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 96 (2026-07-02): Final WatchlistEngine caller audit and migration order decision**

**Decision:** Migrate `atlas/intelligence/` first (Sprint 97), then `atlas/conversation/` (Sprint 98). Do not migrate either in Sprint 96.

**Rationale:**
- Sprint 96 is an audit sprint only. Both remaining callers are more central than prior targets (monitoring, watchlist_review, decision).
- `atlas/intelligence/` is categorically lower risk: `WatchlistAnalysis` content is never rendered or surfaced in user-visible output. The only effect is a confidence bonus (+3 for non-None watchlist) and a passthrough field in `IntelligenceReport`.
- `atlas/conversation/` has a direct WATCHLIST_REVIEW response path that renders six specific `WatchlistAnalysis` fields (`strongest_opportunity`, `cheapest_valuation`, `highest_quality_company`). These have no 1:1 Blueprint equivalents. The semantic shift requires deliberate output design.
- `ConversationEngine.__init__` passes `watchlist_engine=self.watchlist_engine` into `IntelligenceEngine(...)`. Sprint 97 removing this parameter from `IntelligenceEngine.__init__` makes Sprint 97 a prerequisite for Sprint 98's cleanup.

**Alternatives considered:**
- Migrate conversation first: rejected — higher semantic risk, dependent on intelligence migration for clean kwarg removal.
- Migrate both in Sprint 96: rejected — this is a planning sprint; runtime changes require independent test coverage and careful output change documentation.
- Leave both for deletion with WatchlistEngine: rejected — doing the migration first decouples type cleanup from engine deletion.

**Outcome:** Migration plan document created at `docs/WatchlistEngineMigrationPlan.md`. Caller count remains 2. No runtime changes. 1122 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 97 (2026-07-02): Remove WatchlistEngine from `atlas/intelligence/engine.py`**

**Decision:** Replace `IntelligenceEngine` direct `WatchlistEngine` usage with `WatchlistIntelligenceEngine` (Blueprint capability), following the Sprint 95 pattern. Remove `watchlist_engine` from `IntelligenceEngine.__init__`.

**Rationale:**
- Sprint 96 identified this as the lower-risk migration: `WatchlistAnalysis` content was never rendered in any intelligence output string; the only effect was a confidence bonus (+3) and a stored passthrough field.
- `IntelligenceReport.watchlist_intelligence` now carries `WatchlistIntelligenceReport | None` — richer research signals replace legacy scoring output, consistent with Blueprint architecture.
- Removing `watchlist_engine` from `IntelligenceEngine.__init__` simplifies Sprint 98: `ConversationEngine.__init__` no longer needs to pass it through.
- Provider is no longer passed to the watchlist analysis path — `WatchlistIntelligenceEngine` needs no provider, reducing provider coupling.

**Alternatives considered:**
- Keep `WatchlistAnalysis` field in `IntelligenceReport` and only remove the engine param: rejected — would leave stale type annotation; field is a passthrough nobody reads.
- Migrate conversation first: deferred — conversation has deeper semantic coupling (`_answer_watchlist_review()` renders 6 specific WatchlistAnalysis fields with no 1:1 Blueprint equivalents).

**Outcome:** WatchlistEngine caller count reduced 2 → **1** (conversation only).
`atlas/intelligence/engine.py` no longer imports `WatchlistEngine`. `IntelligenceReport.watchlist_intelligence` holds `WatchlistIntelligenceReport | None`. 1124 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 98 (2026-07-02): Remove WatchlistEngine from `atlas/conversation/engine.py`; active caller count → 0**

**Decision:** Rewrite `_answer_watchlist_review()` to use `WatchlistIntelligenceEngine`; adopt research-attention output framing; set confidence to 70 (matching Blueprint monitoring pattern).

**Rationale:**
- This is the final active WatchlistEngine caller. After Sprint 98, the active caller count is zero.
- `_answer_watchlist_review()` previously rendered 6 legacy `WatchlistAnalysis` fields (`strongest_opportunity`, `cheapest_valuation`, `highest_quality_company`, `final_atlas_view`, `name`). None have 1:1 equivalents in `WatchlistIntelligenceReport`, requiring deliberate field mapping.
- Output framing shift from score-ranking to research-attention is intentional: Blueprint watchlist intelligence surfaces research gaps and coverage priorities, not ranked investment scores. Keeping score-ranking language ("Atlas ranks X first") would misrepresent the underlying data source.
- `confidence` changed from 80 to 70 for consistency with the Blueprint monitoring watchlist path (Sprint 93 established 70 as the Blueprint watchlist confidence baseline).
- Provider no longer passed to `_answer_watchlist_review()` — `WatchlistIntelligenceEngine` needs none. This is a provider boundary reduction, not expansion.

**Alternatives considered:**
- Keep `confidence=80`: rejected — 80 was a legacy hardcode unrelated to the Blueprint output; 70 matches the established Blueprint watchlist pattern.
- Map `cheapest_valuation`/`highest_quality_company` to dedicated Blueprint fields: no 1:1 equivalent exists; `evidence_gaps[0].detail` and `observations[0].detail` provide the closest research-coverage substitutes.

**Outcome:** WatchlistEngine active caller count: 1 → **0**. All active callers retired across Sprints 93–98. `WatchlistEngine` and `atlas/analysis/watchlist.py` retained for Sprint 99 deletion. 1124 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 99 (2026-07-02): Delete `WatchlistEngine`; slim `atlas/analysis/watchlist.py` to types only**

**Decision:** Delete `WatchlistEngine`, `WatchlistAnalysis`, `WatchlistSignal`, `WatchlistRecommendation`, and `render_watchlist_analysis` from `atlas/analysis/watchlist.py`. Retain file with `Watchlist` and `WatchlistItem` only. Delete `tests/test_watchlist.py`. Flip guardrail tests.

**Rationale:**
- Active WatchlistEngine caller count reached zero in Sprint 98. Deletion criteria met.
- `atlas/analysis/watchlist.py` cannot be fully deleted: 7 production modules import `Watchlist`/`WatchlistItem` as input types, and `atlas/shared/entities.py`'s `Watchlist` has a different structure (`tickers: tuple[str, ...]` vs `items: tuple[WatchlistItem, ...]`) — not a drop-in substitute.
- Slimming the file to types only achieves the deletion mission for `WatchlistEngine` while preserving the input contract that 7 callers depend on.
- `tests/test_watchlist.py` tested only `WatchlistEngine.analyze()` and `render_watchlist_analysis()` — both removed. No surviving test content; deletion is correct.

**Alternatives considered:**
- Migrate all type-only callers to `atlas/shared/entities.py` `Watchlist` in the same sprint: rejected — different field structure (`tickers` vs `items`) makes this a multi-file semantic migration; deferred to Sprint 100+.
- Full file deletion: rejected — would break 7 production module imports without a substitute type.

**Outcome:** `WatchlistEngine` deleted. `atlas/analysis/watchlist.py` slimmed to 33 lines. `tests/test_watchlist.py` deleted. Guardrails flipped to confirm non-importability. 1119 tests passing (3 skipped).

---

**Sprint 100 (2026-07-02): Post-WatchlistEngine architecture checkpoint; type migration plan created**

**Decision:** No runtime changes. Audit legacy watchlist state; add non-importability guardrails; create `docs/WatchlistTypeMigrationPlan.md`; recommend `WatchlistInput`/`WatchlistInputItem` in `atlas/capabilities/watchlist_intelligence/` as migration destination.

**Rationale:**
- WatchlistEngine deletion is confirmed complete. All deleted symbols (`WatchlistEngine`, `WatchlistAnalysis`, `WatchlistRecommendation`, `render_watchlist_analysis`) pass non-importability guardrails.
- `atlas/analysis/watchlist.py` contains only `Watchlist` and `WatchlistItem` — confirmed by source scan and new guardrail test.
- 7 production modules import `Watchlist`/`WatchlistItem` for CLI input parsing only. None use engine logic. All can be updated with mechanical import path changes in one sprint.
- Recommended destination is `atlas/capabilities/watchlist_intelligence/` (renamed to `WatchlistInput`/`WatchlistInputItem`) because: (a) the type is a capability input, not a domain entity; (b) `atlas/shared` already owns a structurally different `Watchlist`; (c) `atlas/domains/watchlist/` re-exports `atlas.shared.Watchlist` — adding a different `Watchlist` there creates a namespace conflict.

**Alternatives considered:**
- `atlas/shared/entities.py`: rejected — different structure; `from_json_file`/`from_mapping` are CLI input concerns, not canonical entity concerns.
- `atlas/domains/watchlist/`: rejected — namespace conflict with re-exported `atlas.shared.Watchlist`.
- Keep in `atlas/analysis/watchlist.py` permanently: rejected — perpetuates legacy analysis package as a type source.

**Outcome:** No runtime changes. 6 guardrails added. `docs/WatchlistTypeMigrationPlan.md` created. 1125 tests passing (3 skipped). Demo passed. Release verification green. Sprint 101 target: migrate `Watchlist`/`WatchlistItem` to `atlas/capabilities/watchlist_intelligence/` as `WatchlistInput`/`WatchlistInputItem`; delete `atlas/analysis/watchlist.py`.

---

**Sprint 101 (2026-07-02): Move `Watchlist`/`WatchlistItem` to capability layer; delete `atlas/analysis/watchlist.py`**

**Decision:** Add `WatchlistInput`/`WatchlistInputItem` to `atlas/capabilities/watchlist_intelligence/models.py`. Update all 7 production callers and 5 test files. Delete `atlas/analysis/watchlist.py`. No logic changes.

**Rationale:**
- As planned in Sprint 100, the legacy `Watchlist`/`WatchlistItem` were CLI input types that existed in the wrong layer. Moving them to the capability module that owns the watchlist analysis pipeline is Blueprint-aligned.
- Renaming to `WatchlistInput`/`WatchlistInputItem` distinguishes them from the canonical `atlas/shared/entities.py` `Watchlist` (domain entity) and the rich `atlas/capabilities/watchlist_intelligence/models.py` `WatchlistItem` (capability input).
- All 7 production callers used `Watchlist` only as a type annotation or via `from_json_file`/`from_mapping`. All changes were mechanical import path updates and type renames with no logic changes.
- `atlas/cli/deprecations.py` string reference (`legacy_module="atlas.analysis.watchlist"`) is historical metadata — correctly retained as a registry record; not an import.

**Alternatives considered:**
- Compatibility shim in `atlas/analysis/watchlist.py` re-exporting from capability: rejected — Sprint spec explicitly prohibits shims; full deletion achieves cleaner architecture.

**Outcome:** `atlas/analysis/watchlist.py` fully deleted. `atlas.analysis.watchlist` raises `ModuleNotFoundError`. `WatchlistInput`/`WatchlistInputItem` accessible from `atlas.capabilities.watchlist_intelligence`. 1124 tests passing (3 skipped). Demo passed. Release verification green. No behavior changes.

---

**Sprint 102 (2026-07-02): Analysis cleanup audit; `ComparisonEngine` selected as Sprint 103 target**

**Decision:** No runtime changes. Audit `atlas/analysis/` modules; recommend `ComparisonEngine` for Sprint 103 over `MemoryEngine`.

**Rationale:**
- `ComparisonEngine` has 2 production caller sites (both `atlas/decision/`), 0 active CLI commands, no Blueprint gap (legacy ranking; Blueprint `InvestmentComparisonEngine` exists), and a self-contained module with no cross-domain dependencies. Inline ranking option (Option A) can eliminate the engine without output changes.
- `MemoryEngine` has 4 caller sites, 3 active CLI commands (`atlas memory save/show/compare`), no Blueprint equivalent, and user-data coupling (local JSON files). Higher risk and complexity.
- Ordering: `ComparisonEngine` first because it is contained entirely within the decision engine's optional comparison path, with no CLI surface area. `MemoryEngine` deferred to Sprint 104+ pending further audit of `atlas memory` CLI command usage.

**Alternatives considered:**
- `MemoryEngine` first: rejected — 3 active CLI commands and user-data coupling make it higher risk than `ComparisonEngine`.
- Both in one sprint: rejected — two different migration patterns; keeping them separate maintains the sprint-per-engine cleanup discipline that has worked well.

**Outcome:** No runtime changes. `docs/AnalysisCleanupPlan.md` created. 1 guardrail test added. 1125 tests passing (3 skipped). Demo passed. Release verification green. Sprint 103 target: `ComparisonEngine`.

---

**Sprint 103 (2026-07-02): Retire `ComparisonEngine`; delete `atlas/analysis/comparison.py`**

**Decision:** Move `ComparisonResult`/`ComparisonRanking`/`ComparisonCandidate` types and ranking logic to `atlas/decision/comparison.py` as a free function; delete `atlas/analysis/comparison.py`.

**Rationale:**
- Option C (retire comparison path entirely) rejected: `_comparison_tickers()` in decision engine pulls from `context.watchlist.items` when a watchlist is set, making the comparison path active whenever watchlist context is provided.
- Option A (inline ranking) chosen: ranking logic is a simple sort across 5 score dimensions. Moving it to `atlas/decision/comparison.py` as `compare_tickers(tickers, provider, investment_engine)` eliminates the `ComparisonEngine` class, removes the constructor param from `AtlasDecisionEngine`, and preserves identical output.
- `ComparisonResult` retained as a type in `atlas/decision/comparison.py` because it is stored on `DecisionResult` and inspected by one test. Changing the output type would be a behavior change; the type move is location-only.

**Alternatives considered:**
- Option B (route through `InvestmentComparisonEngine`): rejected — heavier, different output format, would change `DecisionResult` shape.
- Keep `ComparisonEngine` class: rejected — no benefit to the class wrapper once callers are 0; free function is cleaner.

**Outcome:** `atlas/analysis/comparison.py` deleted. `atlas.analysis.comparison` raises `ModuleNotFoundError`. `ComparisonResult` et al. importable from `atlas.decision.comparison`. `AtlasDecisionEngine` constructor lost `comparison_engine` param. 4 guardrail tests added. 1125 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 104 (2026-07-02): Retire `MemoryEngine`; delete `atlas/analysis/memory.py`**

**Decision:** Move `MemoryEntry`, `MemoryComparison`, `MemoryStore` types and all logic to `atlas/decision/memory.py` as free functions; delete `atlas/analysis/memory.py`. Pattern identical to Sprint 103.

**Rationale:**
- Option A (delete outright) not viable: 3 active CLI commands (`atlas memory save/show/compare`) and `AtlasDecisionEngine._compare_memory()` are active callers.
- Option B (move to `atlas/decision/memory.py`) chosen: decision engine is primary runtime consumer; CLI importing from `atlas.decision.memory` is architecturally acceptable (CLI sits above all layers).
- `MemoryEngine` class eliminated: `load()` was pure delegation (`store.load()`); `save()` inlined; `save_ticker()` and `compare()` become `save_ticker()` and `compare_memory()` free functions.
- No Blueprint-aligned `MemoryStore[MemoryEntry]` was created — the existing concrete `MemoryStore` class moved as-is to avoid scope creep.

**Alternatives considered:**
- Retain with blockers (Option C): rejected — the logic was small and the migration pattern was proven by Sprint 103.
- Move to `atlas/history/`: rejected — `atlas/history/` uses Blueprint `atlas.memory.MemoryStore[Snapshot]`, a different generic abstraction. Merging would require adapting the type system beyond sprint scope.
- Invent new capability (`atlas/tracking/`): rejected — unnecessary scope; `atlas/decision/memory.py` co-locates the logic with its primary runtime consumer.

**Outcome:** `atlas/analysis/memory.py` deleted. `atlas.analysis.memory` raises `ModuleNotFoundError`. `MemoryEntry`/`MemoryStore`/`MemoryComparison` importable from `atlas.decision.memory`. `AtlasDecisionEngine` constructor lost `memory_engine` param. CLI updated to use free functions. 5 guardrail tests added. 1130 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 105 (2026-07-02): Eliminate `ExplanationEngine` class from `atlas/analysis/explanation.py`**

**Decision:** Inline `ExplanationEngine.explain()` logic directly into `explain_investment_report()` free function. File remains at `atlas/analysis/explanation.py`. `ExplanationEngine` class removed.

**Rationale:**
- `ExplanationEngine` was a one-method class (`explain()`) whose only caller was `explain_investment_report()` itself — no external code ever instantiated it directly.
- `explain_investment_report()` was already the public API; the class added no value beyond an unnecessary level of indirection.
- Moving the file out of `atlas/analysis/` is not viable: `atlas/analysis/report.py` imports `explain_investment_report` and `render_investment_explanation`. Moving to `atlas/decision/` or `atlas/capabilities/` would create a backwards dependency (`atlas/analysis/` → `atlas/decision/`), which is architecturally worse than the current state.
- Option B (in-place class elimination) is the correct action: the class is removed, the module becomes a pure free-function module, no behavior changes.

**Alternatives considered:**
- Move to `atlas/capabilities/explanation/`: rejected — `atlas/analysis/report.py` imports from this module; moving it out creates backwards dependency.
- Move to `atlas/decision/explanation.py`: rejected — same reason; `atlas/analysis/` should not depend on `atlas/decision/`.
- Retain as-is (Option C): rejected — the class provided no value; inline is safe and zero-risk.

**Outcome:** `ExplanationEngine` class deleted from `atlas/analysis/explanation.py`. `explain_investment_report()` is now a direct free function. `atlas/analysis/__init__.py` no longer re-exports `ExplanationEngine`. 3 guardrail tests added. 1133 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 106 (2026-07-02): Eliminate `RecommendationEngine` class from `atlas/analysis/scoring.py`**

**Decision:** Remove `RecommendationEngine` (thin one-method wrapper). Retain `ScoringEngine` (has real validation logic). Update tests to use `ThresholdRecommendationPolicy` directly.

**Rationale:**
- `RecommendationEngine` had one public method (`recommend()`) that delegated entirely to `ThresholdRecommendationPolicy.recommend()`. Constructor just forwarded threshold params. No production caller ever instantiated it — only `tests/test_scoring.py`.
- `ScoringEngine` is not a thin wrapper: it has a 4-check `_validate_weights()` static method, two public methods (`score()`, `confidence()`), and a `weights` constructor param. Elimination would lose the weight validation contract. Retained with documentation noting no production callers exist.
- `score_company()` free function retained — wraps `ScoringEngine` and provides the entry point for weight-injected scoring.

**Alternatives considered:**
- Eliminate `ScoringEngine` too: rejected — has real validation logic tested directly; elimination would lose the `_validate_weights()` contract.
- Move `scoring.py` to `atlas/capabilities/`: rejected — no production caller; not worth the migration overhead for a test-utility module.
- Retain `RecommendationEngine` (Option D): rejected — thin wrapper, zero production callers, identical pattern to `ExplanationEngine` eliminated in Sprint 105.

**Outcome:** `RecommendationEngine` class deleted from `atlas/analysis/scoring.py` and removed from `atlas/analysis/__init__.py`. `tests/test_scoring.py` updated to use `ThresholdRecommendationPolicy` directly. `ThresholdRecommendationPolicy` import removed from `scoring.py`. 3 guardrail tests added. 1136 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 107 (2026-07-02): Audit `atlas/analysis/report.py`; remove unused helper**

**Decision:** Retain `report.py` in place (Option C). Remove `render_company_analysis_report` (no callers). Keep `build_investment_report` and `render_investment_report`.

**Rationale:**
- `build_investment_report` has 3 active CLI call sites (lines 219, 265, 1408 of `atlas/cli/main.py`) and 1 Blueprint engine call site (`atlas/comparison/engine.py:214`). Cannot be deleted or moved without updating 4 call sites.
- `render_investment_report` has 2 active CLI call sites. Same retention reasoning.
- `render_company_analysis_report` was a thin one-liner combining the two functions above. Grep confirmed zero external callers — only its own definition. Removed as dead code.
- Moving the file to a Blueprint-aligned layer would create unnecessary churn — 4 callers would need import updates for no architectural gain. The file belongs where it is.

**Alternatives considered:**
- Delete file: rejected — `build_investment_report` and `render_investment_report` are actively used by CLI and Blueprint comparison engine.
- Move to `atlas/capabilities/`: rejected — would require updating 4 call sites and would create backwards-dependency pressure on `atlas/analysis/explanation.py` (which `report.py` imports).
- Simplify in-place: no simplification available beyond removing the dead helper.

**Outcome:** `render_company_analysis_report` removed from `atlas/analysis/report.py`. No `__init__.py` change needed (function was never exported). 2 guardrail tests added. 1138 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 108 (2026-07-02): Post-cleanup checkpoint for `atlas/analysis/`**

**Decision:** Checkpoint sprint — no runtime changes. `atlas/analysis/scoring.py` selected as Sprint 109 deletion target.

**Rationale:**
- Full inventory audit of `atlas/analysis/` confirmed 15 remaining modules (3 deleted in Sprints 101–107).
- `ScoringEngine` and `score_company` in `scoring.py` have zero production callers — confirmed by grep. Only `tests/test_scoring.py` uses them. This makes `scoring.py` the cleanest remaining deletion target.
- `portfolio.py` has 17 production import sites and 16 test files — too high coupling for near-term migration.
- `engine.py` has 10 production import sites and is the foundational scoring engine — leave for last.
- Blueprint `domains/` confirmed import-free from `atlas.analysis` via new AST-based guardrail test.
- All 3 previously deleted modules (`watchlist`, `comparison`, `memory`) confirmed still absent.

**Guardrails added:**
- `test_blueprint_domains_do_not_import_legacy_analysis` — AST scan confirms `atlas/domains/` never imports from `atlas.analysis`.

**Outcome:** 1 guardrail test added. 1138 tests passing (3 skipped). Demo passed. Release verification green. Sprint 109 target: delete `atlas/analysis/scoring.py`.

---

**Sprint 109 (2026-07-02): Delete `atlas/analysis/scoring.py`**

**Decision:** Delete `atlas/analysis/scoring.py`. Remove `ScoringEngine` and `score_company` from `atlas/analysis/__init__.py`.

**Rationale:**
- Sprint 108 grep confirmed zero production callers for `ScoringEngine` and `score_company` across the entire `atlas/` tree.
- `ScoringEngine` wrapped `AtlasInvestmentEngine` with a 4-check weight validation that was never exercised outside tests.
- No provider or network dependency. No runtime behavior changes.
- Removing the module tightens the public `atlas.analysis` surface and eliminates dead API.

**Alternatives considered:**
- Keep as documented test utility: rejected — public re-exports from `atlas.analysis.__init__` imply production availability; keeping dead API is misleading.
- Move weight validation into `AtlasInvestmentEngine`: out of scope — no production caller needs it.

**Outcome:** `atlas/analysis/scoring.py` deleted. 2 names removed from `atlas/analysis/__init__.py`. `tests/test_scoring.py` stripped of 3 dead tests (2 surviving tests kept). 2 guardrail tests updated. 1136 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 110 (2026-07-02): `atlas/analysis/portfolio.py` migration plan**

**Decision:** Multi-sprint migration required. Sprint 111 is a pre-migration guardrail sprint (Phase 1 of 6 already completed in Sprint 110). Phase 2 (type extraction) and Phase 3 (capability creation) are the next implementation targets.

**Rationale:**
- `PortfolioIntelligenceEngine` has no Blueprint equivalent. Cannot retire the module until `atlas/capabilities/portfolio_intelligence/` exists with equivalent 7-dimension portfolio-fit scoring.
- Schema gap: `PortfolioPosition.quality_score` and `risk_score` are not in `atlas.shared.Holding`. A `PortfolioFitProfile` type or `Holding` extension is needed before provider migration.
- `CompanyPortfolioProfile` is embedded in `CompanyDataProvider.get_portfolio_profile()`. 3 providers must be updated atomically.
- 17 production import sites make a bulk migration unsafe. One caller per sprint is the only safe approach.
- `render_portfolio_analysis` has zero active non-test production callers — can be removed as a low-risk first step in a future sprint.

**Documents created:** `docs/PortfolioAnalysisMigrationPlan.md`

**Guardrails added:** 3 pre-migration tests confirming domain is intact, adapter path is in use, and `render_portfolio_analysis` has no active production callers.

**Outcome:** 3 guardrail tests added. 1139 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 111 (2026-07-02): Delete `render_portfolio_analysis` from `atlas/analysis/portfolio.py`**

**Decision:** Delete `render_portfolio_analysis`. Also delete `_score_line` and `_signal_line` private helpers (only used by the deleted function). Remove re-export from `atlas/analysis/__init__.py`.

**Rationale:**
- Sprint 110 guardrail test confirmed zero active production callers. Only `atlas/analysis/__init__.py` re-exported it and `tests/test_portfolio.py` tested it.
- `render_portfolio_analysis` was the output renderer for the retired `atlas portfolio analyze` CLI command (retired Sprint 89). No active CLI command or engine calls it.
- The `_score_line` and `_signal_line` helpers were internal to `render_portfolio_analysis` and have no other callers.
- No provider or network dependency. Pure rendering logic.

**Outcome:** 3 symbols deleted from `portfolio.py`. 1 re-export removed from `__init__.py`. 1 test removed from `tests/test_portfolio.py`. 2 guardrail tests added. 1139 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 112 (2026-07-02): Create `atlas/capabilities/portfolio_intelligence/` stub**

**Decision:** Create new capability package with `PortfolioFitInput`, `PortfolioFitResult`, and `PortfolioFitDimension`. Omit `recommendation` enum from `PortfolioFitResult`. Rename `portfolio_score` → `fit_score`, `final_reasoning` → `summary`, `reasoning` → `note`.

**Rationale:**
- Blueprint layer must not carry advisory semantics (`PortfolioRecommendation.STRONG_ADD` / `ADD` / `REDUCE` etc.) — these belong to the legacy layer or to future user-facing rendering only.
- `fit_score` is more neutral than `portfolio_score` — it describes analytical output, not a grade.
- `summary` is more neutral than `final_reasoning` — the legacy field name implies a recommendation path.
- `note` vs `reasoning` — `PortfolioFitDimension.note` avoids the implication that a score requires a justification/argument rather than a factual observation.
- All legacy fields preserved where semantically equivalent — `ticker`, `company`, `sector`, `country`, `market_cap`, `quality_score`, `risk_score` are direct mappings.
- No provider or network dependency introduced. No existing callers changed.

**Outcome:** 3 new types. 12 tests. Boundary constraints verified by AST scan in tests. 1151 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 113 (2026-07-02): Implement `PortfolioIntelligenceCapability` engine**

**Decision:** Port 7-dimension scoring logic from `atlas/analysis/portfolio.py` into `atlas/capabilities/portfolio_intelligence/engine.py` as a new `PortfolioIntelligenceCapability` class. Accept `atlas.shared.Portfolio` (not legacy `Portfolio`). Document schema gap rather than working around it.

**Rationale:**
- Logic is ported, not wrapped — the new engine does not import `PortfolioIntelligenceEngine` or any legacy analysis symbol. This preserves the clean architecture boundary.
- `atlas.shared.Portfolio` is the correct input type for the Blueprint layer. Using the legacy `atlas.analysis.portfolio.Portfolio` would violate the architectural boundary.
- Schema gap (`atlas.shared.Holding` lacks `quality_score`, `risk_score`, `market_cap`) is real and affects 3 of 7 dimensions. Returning neutral scores with documented notes is correct: callers will know what's partial, and future `atlas.shared.Holding` extension will resolve these gaps without breaking callers.
- Weights in `_aggregate_fit_score` mirror the legacy exactly — this is intentional so aggregate behavior is comparable even while individual dimensions differ.
- No callers migrated — the legacy engine remains the active production path. This sprint adds capability alongside, not in replacement.

**Outcome:** `PortfolioIntelligenceCapability` engine created. 30 tests. 1181 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 114 (2026-07-02): Resolve schema gap; migrate conversation portfolio-fit to capability**

**Decision 1: Extend `atlas.shared.Holding` (Option A) rather than create `PortfolioFitHolding` (Option B)**

**Rationale:**
- `quality_score`, `risk_score`, `market_cap` make semantic sense on a holding entity — they are attributes of the underlying position, not capability-specific enrichment.
- Only 6 `Holding(...)` instantiation sites; all use keyword args; optional fields (default None) cause zero blast radius.
- Adapter already converts `PortfolioPosition` → `Holding`; natural place to carry enriched fields.
- Option B would have required an extra conversion layer and a capability-specific type with no shared value.

**Decision 2: Retain `portfolio_engine: PortfolioIntelligenceEngine` for `IntelligenceEngine` injection**

**Rationale:**
- Sprint spec: "do not migrate other callers." `IntelligenceEngine` is a separate caller.
- Adding `portfolio_fit_capability` as a second injectable allows conversation's own portfolio review path to use the new capability without touching `IntelligenceEngine`.
- This is the minimal-impact approach — exactly one path changes; all other paths unchanged.

**Decision 3: Keep `ConversationInput.portfolio: Portfolio | None` typed as legacy `Portfolio`**

**Rationale:**
- Changing the type would require updating `atlas/cli/main.py` (which builds `ConversationInput`), which is explicitly out of scope.
- The adapter conversion (`legacy_portfolio_to_domain_portfolio`) happens inside `_answer_portfolio_review` — the legacy Portfolio is converted to `atlas.shared.Portfolio` on the fly. No API surface change.

**Outcome:** 5 files changed. 13 new tests. 1194 tests passing (3 skipped). Demo passed. RC2 green.

---

**Sprint 115 (2026-07-02): Migrate dashboard portfolio-fit to capability**

**Decision:** Same pattern as Sprint 114. `portfolio_engine` retained in constructor for backward compatibility but is no longer called internally. `portfolio_fit_capability` added alongside it.

**Rationale:**
- The `if target_ticker and provider:` block is the only place `portfolio_engine` is used in the dashboard. Migrating just that block leaves the rest of the dashboard (suitability, risk drift, monitoring) untouched.
- Keeping `portfolio_engine` in the constructor is deliberate: it avoids breaking any caller that injects a mock for the old engine in tests, and preserves the public API surface until deletion is safe.
- Field mapping is direct: `portfolio_score` → `fit_score`, `final_reasoning` → `summary`.

**Outcome:** 2 files changed. 6 new tests. 1200 tests passing (3 skipped). Demo passed. RC2 green.

**Sprint 116 (2026-07-02): Migrate portfolio_review internal structural functions to shared Portfolio**

**Decision:** Unlike conversation/dashboard (one isolated block), `portfolio_review/engine.py` uses legacy `Portfolio.positions` throughout 8 private helpers. Migration approach: convert to `shared_portfolio = legacy_portfolio_to_domain_portfolio(review_input.portfolio)` at the top of `review()`, pass `shared_portfolio` to all structural functions, keep `review_input.portfolio` (legacy) for suitability/risk_drift/monitoring downstream. Input boundary type stays `LegacyPortfolio` — the CLI and downstream engines are unchanged.

**Rationale:**
- The entire engine is structural analysis (sectors, weights, quality averages, concentrations) — not portfolio-fit via `PortfolioIntelligenceCapability`. The "migration" here is removing `portfolio.positions` coupling from internal helpers by routing through the shared type.
- Keeping `LegacyPortfolio` at `PortfolioReviewInput.portfolio` avoids cascading changes to suitability, risk_drift, and monitoring engines (all still expect legacy `Portfolio`).
- `_average` updated to handle `quality_score: int | None` (Sprint 114 made it optional on `Holding`) via None-safe list comprehension.

**Outcome:** 2 files changed. 7 new tests. 1207 tests passing (3 skipped). Demo passed. RC2 green.

**Sprint 117 (2026-07-02): Adapter audit checkpoint — centralize PortfolioFitInput builder**

**Decision:** Option C — Centralize `PortfolioFitInput` builder. `legacy_portfolio_to_domain_portfolio` was already centralized. `PortfolioFitInput` construction (7-field 1-to-1 mapping from `CompanyPortfolioProfile`) was verbatim duplicate across conversation and dashboard. Extracted `portfolio_fit_input_from_profile` into `atlas/adapters/portfolio.py`. Portfolio review does not build `PortfolioFitInput` (structural-only path) and is unaffected.

**Rationale:**
- Duplication was genuine and mechanical: identical 7-line block in 2 callers.
- `atlas/adapters/portfolio.py` is the correct home: it already mediates between legacy and Blueprint types; adding `CompanyPortfolioProfile → PortfolioFitInput` conversion is consistent with its purpose.
- Capability engine remains clean: no legacy imports enter `atlas/capabilities/portfolio_intelligence/engine.py`.
- Keeping legacy `PortfolioFitInput` import in conversation/dashboard would have been dead weight after centralization.

**Outcome:** 4 files changed (adapter + 2 callers + new test file). 31 new tests. 1238 tests passing (3 skipped). Demo passed. RC2 green. Recommended Sprint 118: `atlas/reasoning/engine.py`.

**Sprint 118 (2026-07-02): Remove reasoning PortfolioAnalysis direct runtime import**

**Decision:** Option D — TYPE_CHECKING-only import. `PortfolioAnalysis` had runtime field accesses in `_collect_evidence` and `_bearish_factors`, but these are duck-typed attribute accesses that do not require the import at runtime. Added `from __future__ import annotations` (PEP 563) so the type annotation in `ReasoningInput.portfolio_analysis: PortfolioAnalysis | None` becomes a string at class-definition time, eliminating the need for the name to be defined at runtime.

**Rationale:**
- `from __future__ import annotations` is the correct tool: it defers annotation evaluation without changing any runtime behavior.
- `TYPE_CHECKING` guard keeps type checkers (mypy/pyright) fully aware of the type.
- No runtime field access requires an import — Python's duck typing handles attribute access on whatever object is passed.
- Transitive loading of `atlas.analysis.portfolio` via `atlas.analysis.__init__` is a pre-existing package coupling not introduced by reasoning/engine.py — fixing it is out of scope.

**Outcome:** 2 files changed (engine + test). 7 new tests. 1245 tests passing (3 skipped). Demo passed. RC2 green. Recommended Sprint 119: `atlas/risk_drift/engine.py`.

**Sprint 134 (2026-07-02): Planning sprint — audit `Portfolio`/`PortfolioPosition` remaining callers**

**Decision:** Sprint 135 target is "lift and shift" — move `Portfolio`, `PortfolioPosition`, and 2 private helpers from `atlas/analysis/portfolio.py` into `atlas/adapters/portfolio.py` and delete the source file in the same sprint.

**Rationale:**
- All 12 production import sites are now mapped (3 runtime + 1 re-export + 8 annotation-only).
- `atlas/adapters/portfolio.py` is the correct destination: already the legacy compatibility boundary, already imports `LegacyPortfolio`; making it self-contained eliminates the circular dependency direction.
- `atlas.shared.Portfolio` and `atlas.shared.Holding` are NOT drop-in replacements — different container field names (`.holdings` vs `.positions`) and no JSON loading methods. Migrating to them would require changing all 4 engines that access `.positions` directly, plus moving JSON loading out of the types entirely.
- Single-sprint completion avoids a "shim sprint" (move + keep stale re-export) that would need its own guardrail tests.
- `PortfolioPosition` has zero production runtime callers outside `portfolio.py` itself — it can only move alongside `Portfolio`.

**Outcome:** Caller map documented. Sprint 134 guardrail tests added. 1352 tests passing (3 skipped). Demo passed. RC2 green.

---

**Sprint 138 (2026-07-02): Analysis package checkpoint**

**Decision:** Audit-only sprint. No deletions, no migrations. Document the current `atlas/analysis/` state now that the portfolio migration is fully resolved.

**Findings:**
- 13 modules remain. Portfolio migration has reduced the package from 17 modules (Sprint 108) to 13.
- `engine.py` (foundational) — 11 production callers (`conversation`, `decision/*`, `intelligence`, `monitoring`, `reasoning`, `suitability`, `models`, `adapters`). Do not touch until a Blueprint replacement exists.
- `scores.py` (shared utility, 2 lines) — 10 production callers across 7 packages. Do not move without a broad refactor.
- `company_analysis.py`, `explanation.py`, `report.py` — active modules, no cleanup needed.
- 7 placeholder submodules (`growth`, `macro`, `moat`, `quality`, `sentiment`, `technicals`, `valuation`): each 18 lines, structurally identical, zero external production callers. Only imported by `company_analysis.py`. Sprint 139 consolidation target.
- `atlas/analysis/__init__.py`: 12 active exports, no stale symbols. `Portfolio` and `PortfolioPosition` confirmed absent.
- `atlas/capabilities/company_analysis/` exists but uses an entirely different model (`CompanyAnalysisReport`) — not a replacement for the legacy analysis layer.
- No Atlas Edge naming encountered.

**Sprint 139 target:** Consolidate the 7 identical-pattern placeholder submodules into `company_analysis.py` and delete the 7 files.

**Outcome:** Docs updated. No runtime changes. 1359 tests passing (3 skipped). Demo passed. RC2 green.

---

**Sprint 137 (2026-07-02): Delete `portfolio_fit_input_from_profile` identity adapter**

**Decision:** Remove the no-op identity function and update the 4 engine callers to call `provider.get_portfolio_profile()` directly.

**Rationale:**
- `portfolio_fit_input_from_profile(profile: PortfolioFitInput) -> PortfolioFitInput` was a pure identity (`return profile`) — adding it to the call chain had zero effect on runtime behavior.
- Sprint 133 retained it to avoid touching 4 engine callers; Sprint 135 and 136 confirmed the adapter boundary is stable enough to make the cleanup safe.
- Removing it makes the provider contract explicit in each engine: `fit_input = provider.get_portfolio_profile(ticker)`.

**Outcome:** `portfolio_fit_input_from_profile` deleted. 4 production files updated. 9 test functions updated. `atlas/adapters/portfolio.py` now contains only meaningful portfolio boundary utilities. 1359 tests passing (3 skipped). Demo passed. RC2 green. Portfolio migration fully resolved.

---

**Sprint 136 (2026-07-02): Post-portfolio migration checkpoint**

**Decision:** No code changes to runtime behavior. Verified architecture post-Sprint 135 deletion.

**Findings:**
- Zero active production imports of `atlas.analysis.portfolio` (AST-confirmed).
- `atlas.analysis.__init__` exports no Portfolio/PortfolioPosition symbols.
- `atlas/adapters/portfolio.py` is self-contained: no CLI, provider, or deleted-module imports.
- All 5 deleted portfolio symbols (PortfolioIntelligenceEngine, PortfolioAnalysis, PortfolioSignal, PortfolioRecommendation, CompanyPortfolioProfile) absent from adapter.
- `atlas/analysis/` inventory: 13 modules. No migration candidates identified for immediate deletion.
- `portfolio_fit_input_from_profile` is a no-op identity function still called by 4 engines (conversation, dashboard, intelligence, decision) — deferred from Sprint 133.

**Sprint 137 target:** Remove `portfolio_fit_input_from_profile` identity adapter from 4 engine callers and delete the function. It is a no-op added in Sprint 133 to avoid touching callers; those callers can now call provider methods directly.

**Outcome:** 4 guardrail tests added. Stale tracking text updated. 1365 tests passing (3 skipped). Demo passed. RC2 green.

---

**Sprint 135 (2026-07-02): Delete `atlas/analysis/portfolio.py`; move types to `atlas/adapters/portfolio.py`**

**Decision:** "Lift and shift" — `Portfolio`, `PortfolioPosition`, `_position_from_mapping`, `_normalize_weight` moved from `atlas/analysis/portfolio.py` into `atlas/adapters/portfolio.py`. `atlas/analysis/portfolio.py` deleted. All 12 production import sites updated atomically in the same sprint.

**Rationale:**
- `atlas/adapters/portfolio.py` is the correct destination: already the legacy compatibility boundary; making it self-contained removes the only remaining coupling back into `atlas/analysis/`.
- Doing the file deletion and all caller updates in one sprint avoids a partial-migration window where two modules each claim ownership.
- No runtime behavior changed: `Portfolio.from_mapping`, `from_json_file`, field access all identical.

**Outcome:** `atlas/analysis/portfolio.py` deleted. `atlas/analysis/` now contains only active modules: `engine.py`, `explanation.py`, `report.py`, `scores.py`, `providers.py`. Sprint 135 guardrail block added to `test_portfolio_analyze_deprecation.py`. Stale "is importable" assertions flipped in 5 test files. 1361 tests passing (3 skipped). Demo passed. RC2 green.

---

**Sprint 133 (2026-07-02): Delete `CompanyPortfolioProfile`; migrate providers to `PortfolioFitInput`**

**Decision:** Option A (thin identity adapter). Updated `CompanyDataProvider.get_portfolio_profile()` return type across all 3 provider files to `PortfolioFitInput`. Changed `portfolio_fit_input_from_profile` to identity function rather than removing it — avoids touching 4 engine callers (conversation, dashboard, intelligence, decision) and their tests.

**Rationale:**
- `CompanyPortfolioProfile` and `PortfolioFitInput` have identical fields (1-to-1 mapping), making the provider switch mechanical with no data loss.
- Option A (identity adapter) minimizes blast radius vs Option B (remove adapter and update engine callers): 4 engine files + their tests left untouched. Adapter cleanup deferred to a future sprint.
- Zero active production callers remained after providers were updated — deletion confirmed safe.

**Outcome:** `portfolio.py` reduced to 59 lines — only `Portfolio` and `PortfolioPosition` remain. All portfolio intelligence types now live in `atlas/capabilities/portfolio_intelligence/`. 1352 tests passing (3 skipped). Demo passed. RC2 green.

---

**Sprint 119 (2026-07-02): Migrate risk drift portfolio dependency**

**Decision:** Two-part migration. (1) `Portfolio`: TYPE_CHECKING guard only — duck-typed `.positions` access preserved because CLI and portfolio_review both pass legacy Portfolio; changing callers is out of scope. (2) `PortfolioAnalysis`: fully replaced by `PortfolioFitResult` from capabilities — this was dead code (no caller passes non-None), making it a safe forward migration.

**Rationale:**
- `_current_largest_weight` accesses `portfolio.positions` — this is duck-typed and continues to work for legacy Portfolio passed by callers. Moving `Portfolio` behind TYPE_CHECKING removes the runtime import without breaking anything.
- `current_portfolio_analysis: PortfolioAnalysis | None` was always None at runtime. Replacing with `PortfolioFitResult | None` is forward-aligned: future callers can pass `PortfolioFitResult` directly from the capability engine, enabling richer concentration context.
- `.overlap_with_existing_holdings.score` → `.overlap.score` because `PortfolioFitResult` uses `overlap` as the field name (per models.py mapping).

**Outcome:** 2 files changed (engine + test). 9 new tests. 1254 tests passing (3 skipped). Demo passed. RC2 green. Recommended Sprint 120: `atlas/suitability/engine.py`.

---

**Sprint 223 (2026-07-04): Define Snapshot Draft schema**

**Decision:** Create `atlas/snapshot_input/` package with formal Snapshot Draft schema. `SnapshotType` (8 values), `SnapshotConfirmationStatus` (5 states), `SnapshotConfidence` (4 levels), `SnapshotDraft` dataclass, `validate_snapshot_draft`, `to_dict`/`from_dict`/`to_json`/`from_json` serialization helpers, `load_snapshot_draft`/`save_snapshot_draft` file helpers. Three example draft files under `examples/snapshot_drafts/`.

**Rationale:** After research notes created the first local bridge from user-supplied material into Weekly Review, Atlas defines a formal draft schema so future Snapshot Input modes can produce structured, confirmable local drafts before updating portfolio, watchlist, journal, research notes, or company facts inputs.

**Outcome:** `atlas/snapshot_input/__init__.py` and `schema.py` created. Three example JSON drafts created. 72 new tests. 2231 tests passing. No Weekly Review behavior changed. Sprint 224 target: Add snapshot draft CLI validation.

---

**Sprint 227 (2026-07-04): Add snapshot draft confirmation planning**

**Decision:** Define the formal confirmation workflow for Snapshot Drafts. New document `docs/SnapshotDraftConfirmationWorkflow.md` specifies: 11 confirmation principles, definitions for all five confirmation states, exportability rules, a review checklist, blocking rules, a field correction model (revised-draft approach), future CLI command shapes (`review`, `confirm`, `reject`, `supersede`), export command dependency, audit/traceability expectations, safety boundary, and relationship to Weekly Review.

**Rationale:** Export commands correctly enforce `confirmation_status == confirmed`, but there was no documented workflow for how a draft reaches that state. Before adding more conversion types, the confirmation boundary must be consistently specified so every future export command follows the same upstream user-review rules.

**Outcome:** `docs/SnapshotDraftConfirmationWorkflow.md` created. No runtime behavior changes. No new CLI commands. 57 new documentation and regression tests. 2384 tests passing. Sprint 228 target: Add `atlas snapshot review` command.

---

**Sprint 226 (2026-07-04): Third real portfolio trial with exported research notes**

**Decision:** Run end-to-end validation of the Snapshot conversion loop. Three confirmed `research_notes_snapshot` drafts (ASML, XYL, NOVO) were validated, exported, and consumed by `atlas weekly-review --research-notes DIR`. Sections 8, 9, and 10 were evaluated in both the example bundle and realistic bundle.

**Rationale:** After implementing the first safe Snapshot Draft conversion path in Sprint 225, Atlas validates the end-to-end loop from confirmed draft to exported research notes to Weekly Review before adding more conversion types or broader confirmation workflows.

**Outcome:** Loop validated as functional, useful, and safe. No code changes required — trial confirmed existing behavior is correct. Two additional confirmed draft examples added (XYL, NOVO). Full trial findings documented in `docs/SnapshotResearchNotesTrialFindings.md`. 2327 tests passing. Sprint 227 target: Add snapshot draft confirmation planning.

---

**Sprint 225 (2026-07-04): Implement confirmed research_notes_snapshot export**

**Decision:** Add `atlas snapshot export-research-notes <draft_path> --output-dir DIR` — the first safe Snapshot Draft conversion path. Converts a confirmed `research_notes_snapshot` draft to a local `research_notes/<TICKER>/notes.md` file. Enforces: type must be `research_notes_snapshot`, status must be `confirmed`, ticker must be present and safe. Existing files blocked without `--overwrite`. Output is bounded (500 chars/bullet, 20 bullets/section). Draft file is never mutated.

**Rationale:** Research notes is the safest first conversion target — no portfolio, watchlist, journal, or company facts files are touched. The end-to-end path (confirmed draft → notes.md → Weekly Review Sections 8/9/10) can now be exercised before adding more conversion types.

**Outcome:** `atlas/snapshot_input/export.py` created. `atlas/snapshot_input/render.py` extended with export render functions. `atlas/snapshot_input/__init__.py` updated. `atlas/cli/main.py` extended with `export-research-notes` command. Confirmed example draft added. 52 new tests. 2327 tests passing. Sprint 226 target: Third real portfolio trial with exported research notes.

---

**Sprint 224 (2026-07-04): Add Snapshot Draft CLI validation**

**Decision:** Add `atlas snapshot validate <path>` — a read-only CLI command that loads a Snapshot Draft JSON file, validates the schema, and renders a human-readable summary (type, confidence, confirmation status, uncertainties, missing fields, safety boundary). Exit 0 on valid, exit 1 on invalid. No file writing, no mutation.

**Rationale:** The draft schema (Sprint 223) needed a way for users to verify drafts before the confirmation workflow is built. A validation command provides immediate value without introducing any write path, provider dependency, or AI.

**Outcome:** `atlas/snapshot_input/render.py` created. `atlas/snapshot_input/__init__.py` updated. `atlas/cli/main.py` extended with `snapshot_app` Typer sub-group and `validate` command. 44 new tests. 2275 tests passing. Sprint 225 target: TBD.

---

**Sprint 222 (2026-07-04): Add research notes input to Weekly Review**

**Decision:** Add an optional `--research-notes DIR` CLI argument that loads per-ticker Markdown notes files (`research_notes/<TICKER>/notes.md`) into Weekly Review. New `WeeklyReviewResearchNote` dataclass. New `_parse_research_notes` function extracts evidence gaps, open questions, risks to monitor, and reasons to wait from known `##` headings. Bounded file reading (8,000 chars max). Section 8 shows evidence gaps from notes; Section 9 shows open questions and risks; Section 10 shows reasons to wait.

**Rationale:** Research notes provide the safest first bridge from Snapshot Input to Weekly Review. Local notes allow users to bring their own analysis, external excerpts, and manual observations into the review without OCR, AI, broker integration, live data, or external research fetching.

**Outcome:** `atlas/weekly_review/inputs.py` extended with `WeeklyReviewResearchNote`, `WeeklyReviewInputPaths.research_notes_dir`, and loader. `render.py` updated for Sections 1, 8, 9, 10, and Input Status. `atlas/cli/main.py` extended with `--research-notes`. Two example files added. 45 new tests. 2159 tests passing. Sprint 223 target: Define Snapshot Draft schema.

---

**Sprint 221 (2026-07-04): Specify Snapshot / Screenshot Input workflow**

**Decision:** Specify the future Snapshot / Screenshot Input workflow as a product document. No implementation. New document `docs/AtlasSnapshotInputWorkflow.md` defines seven snapshot types, a classification contract, a draft contract, a confirmation workflow, accuracy and safety guardrails, a privacy and security boundary, mapping to Weekly Review local inputs, and the relationship to future chat-first workspace UX.

**Rationale:**
After the local-only Weekly Review output was validated and simplified in Sprint 220, Atlas can now define the next low-friction input layer. Snapshot Input should make it easier for users to provide portfolios, watchlists, orders, news, and research notes while preserving confirmation, local-first storage, and structured Weekly Review inputs. Specifying this as a document sprint keeps the v1 foundation unchanged while establishing the product direction for Sprint 222 and beyond.

**Outcome:** `docs/AtlasSnapshotInputWorkflow.md` created. No runtime behavior changed. No provider or network imports introduced. 2078 tests still passing. Sprint 222 target: Add research notes input.
