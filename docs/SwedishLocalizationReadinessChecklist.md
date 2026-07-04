# Swedish Localization Readiness Checklist

**Sprint:** 248
**Date:** 2026-07-04
**Status:** Checklist only — `sv` is not enabled — no Swedish output implemented

---

## Purpose

This document defines the exact go/no-go criteria that must all be satisfied
before `"sv"` may be added to `atlas/locale_support.py`.

It is the operational complement to `docs/SwedishSafeLanguageGuardrails.md`,
which defines the safety layer. This checklist defines the readiness layer:
what code must exist, what tests must pass, and what documentation must be in
place before Swedish output is activated.

A future sprint that wants to enable `sv` must work through this checklist
top to bottom. Every blocking criterion must be green. Non-blocking criteria
should be documented as known gaps if deferred.

---

## Scope

This checklist covers:

- Guardrail coverage criteria
- String constants readiness criteria
- Renderer readiness criteria
- Test coverage criteria
- Documentation readiness criteria
- CLI readiness criteria
- Current status for each criterion (as of Sprint 248)
- How to activate `sv` once all blocking criteria are satisfied

---

## Non-Goals

This document does not:

- Enable Swedish output
- Add `sv` to `atlas/locale_support.py`
- Implement a Swedish renderer
- Translate any runtime string
- Add `--language` to the CLI
- Define French readiness criteria (separate document)

---

## Blocking Criteria

All of the following must be satisfied before `sv` is enabled. A criterion
marked **OPEN** is not yet satisfied. A criterion marked **DONE** is complete.

### B1 — Swedish Safe-Language Guardrail Specification

**Status: DONE (Sprint 247)**

`docs/SwedishSafeLanguageGuardrails.md` must exist and define:

- [ ] All 7 prohibited language categories with guardrail-context-only examples
- [ ] Safe Swedish alternatives table covering all Atlas safe-language concepts
- [ ] Atlas concept mapping for Weekly Review and Snapshot CLI
- [ ] Swedish Weekly Review style rules
- [ ] Swedish Snapshot CLI style rules
- [ ] User-provided content handling rules
- [ ] Testing requirements before `sv` can be enabled

All items above are satisfied by Sprint 247.

---

### B2 — Swedish Localization Readiness Checklist

**Status: DONE (Sprint 248)**

`docs/SwedishLocalizationReadinessChecklist.md` must exist (this document).
The checklist must be reviewed and all blocking criteria assessed before
activation begins.

---

### B3 — Swedish String Constants Module

**Status: DONE (Sprint 249)**

`atlas/weekly_review/strings_sv.py` exists with:

- [x] All 10 section titles in Swedish matching the approved concept mapping
- [x] `WEEKLY_REVIEW_TITLE` in Swedish
- [x] All label constants in Swedish (`LABEL_EVIDENCE_GAP` → `Underlagslucka`, etc.)
- [x] All `INPUT_STATUS_*` message templates in Swedish
- [x] `WARNING_ROW` and `WARNING_SCOPE_SUMMARY` in Swedish
- [x] `WEEKLY_REVIEW_DISCLAIMER` two-line form in Swedish
- [x] All Swedish strings verified against `docs/SwedishSafeLanguageGuardrails.md`
  safe alternatives table and concept mapping

`atlas/snapshot_input/strings_sv.py` exists with:

- [x] All Snapshot CLI headings in Swedish (validation, review, confirm, reject,
  export-research-notes, export-company-facts)
- [x] Safety boundary text in Swedish (`Säkerhetsgräns`)
- [x] Status display strings in Swedish (exportable, blocked, confirmed, etc.)

---

### B4 — Swedish Renderer Dispatch Boundary

**Status: DONE (Sprint 250)**

`atlas/weekly_review/render.py` has a locale-to-strings dispatch helper:

- [x] `_strings_for_locale(locale)` dispatch helper defined
- [x] Helper calls `ensure_supported_locale(locale)` before dispatching (sv remains blocked)
- [x] `locale == "sv"` branch maps to `strings_sv` module (unreachable until B5)
- [x] `locale == "en"` (default) returns `strings_en` module
- [x] `render_weekly_review(result, locale="sv")` raises `ValueError` via `ensure_supported_locale`
- [x] Default English output unchanged

`atlas/snapshot_input/render.py` has a locale-to-strings dispatch helper:

- [x] `_strings_for_locale(locale)` dispatch helper defined
- [x] Helper calls `_ensure_locale(locale)` before dispatching (sv remains blocked)
- [x] `locale == "sv"` branch maps to `strings_sv` module (unreachable until B5)
- [x] `locale == "en"` (default) returns `strings_en` module
- [x] All 14 public renderer functions raise `ValueError` for `locale="sv"`
- [x] Default English output unchanged

Full Swedish output (B7–B10) is gated behind B5. The dispatch boundary is a
structural prerequisite only — sv is still unsupported at runtime.

---

### B5 — `atlas/locale_support.py` Updated

**Status: DONE (Sprint 251)**

`atlas/locale_support.py` adds `"sv"` to its supported set:

- [x] `SUPPORTED_LOCALE_SV = "sv"` constant defined
- [x] `ensure_supported_locale` updated to accept `"sv"` without raising
- [x] `ensure_supported_locale("en")` still passes
- [x] `ensure_supported_locale("fr")` still raises (French not yet enabled)
- [x] `ensure_supported_locale("de")` still raises

---

### B6 — Swedish Forbidden-Category Scan Tests

**Status: DONE (Sprint 252)**

`tests/test_swedish_output_matrix_sprint252.py` generates Swedish output from
all direct renderer calls and scans for all 7 prohibited categories:

- [x] Test verifies no Category 1 phrasing (recommendation language) in generated output
- [x] Test verifies no Category 2 phrasing (transaction/execution language) in generated output
- [x] Test verifies no Category 3 phrasing (price-target language) in generated output
- [x] Test verifies no Category 4 phrasing (urgency language) in generated output
- [x] Test verifies no Category 5 phrasing (certainty/promise language) in generated output
- [x] Test verifies no Category 6 phrasing (outperformance prediction) in generated output
- [x] Test verifies no Category 7 phrasing (personalized advice framing) in generated output

Scan covers rendered output from Weekly Review, Snapshot validation, review,
confirm, reject, research notes export, and company facts export.

---

### B7 — Swedish Heading Output Tests

**Status: DONE (Sprint 252)**

`tests/test_swedish_output_matrix_sprint252.py` verifies all 10 section titles:

- [x] Section 1 → `1. Granskningens omfattning`
- [x] Section 2 → `2. Portföljkontext`
- [x] Section 3 → `3. Bevakningslista`
- [x] Section 4 → `4. Bolagsgranskningar som behöver uppmärksamhet`
- [x] Section 5 → `5. Portföljpassning och lämplighetsnoteringar`
- [x] Section 6 → `6. Risk- och principgränser`
- [x] Section 7 → `7. Öppna beslut`
- [x] Section 8 → `8. Saknat underlag`
- [x] Section 9 → `9. Uppföljningsfrågor`
- [x] Section 10 → `10. Icke-åtgärder / skäl att avvakta`

---

### B8 — Swedish Label Output Tests

**Status: DONE (Sprint 252)**

`tests/test_swedish_output_matrix_sprint252.py` verifies label rendering:

- [x] `Evidence Gap` → `Underlagslucka` in Swedish output
- [x] `Risk to Monitor` → `Risk att följa` in Swedish output
- [x] `Reason to Wait` → `Skäl att avvakta` in Swedish output
- [x] `Decision Deferred` → `Beslut uppskjutet` in Swedish output
- [x] `No Action Warranted` → `Ingen åtgärd motiverad` in Swedish output
- [x] `Watchlist` → `Bevakningslista` in Swedish output
- [x] Input status section → `Indatastatus` in Swedish output
- [x] Input warnings section → `Indatavarningar` in Swedish output
- [x] Portfolio loaded template → `Portfölj: N innehav inlästa.`
- [x] Warning count template → `Varningar: N` in Swedish output
- [x] Missing optional input → `Saknat valfritt indata` in Swedish output

---

### B9 — Swedish Disclaimer Output Test

**Status: DONE (Sprint 252)**

`tests/test_swedish_output_matrix_sprint252.py` verifies the disclaimer:

- [x] Line 1: `Atlas veckovis investeringsgranskning — deterministisk, lokal, utan rekommendationer.`
- [x] Line 2: `Atlas stöder bättre omdöme. Det ersätter det inte.`
- [x] No Category 1–7 phrasing present in disclaimer (covered by B6 scan)
- [x] English disclaimer lines not present in Swedish output

---

### B10 — Swedish Snapshot CLI Heading Tests

**Status: DONE (Sprint 252)**

`tests/test_swedish_output_matrix_sprint252.py` verifies all Snapshot headings:

- [x] `Snapshot Draft Validation` → `Validering av Snapshot Draft`
- [x] `Snapshot Draft Review` → `Granskning av Snapshot Draft`
- [x] `Snapshot Draft Confirmation` → `Bekräftelse av Snapshot Draft`
- [x] `Snapshot Draft Rejection` → `Avvisning av Snapshot Draft`
- [x] `Research Notes Export` → `Export av analysnotisar`
- [x] `Company Facts Export` → `Export av företagsfakta`
- [x] `Safety Boundary` → `Säkerhetsgräns:` (all commands)
- [x] Swedish status labels: `Status: giltig`, `Status: bekräftad`, `Status: avvisad`
- [x] Safety boundary safety lines verified (validate, review, confirm, reject)

---

### B11 — Canonical Value Preservation Tests

**Status: OPEN**

Tests must verify that Swedish-locale output does not translate internal values:

- [ ] `confirmed`, `rejected`, `draft`, `needs_user_review` appear as-is in
  any JSON output written by Swedish-locale commands
- [ ] Warning codes appear as-is in Swedish output (e.g. `missing_optional_profile`)
- [ ] Ticker symbols appear unchanged (`MSFT`, `ASML`, `NOVO`, etc.)
- [ ] Schema keys appear unchanged in any written files

---

### B12 — User-Provided Content Passthrough Tests

**Status: OPEN**

Tests must verify that user-provided content is not modified in Swedish-locale output:

- [ ] Research notes loaded from disk appear unmodified in Swedish Weekly Review output
- [ ] Scope notes appear unmodified in Swedish Weekly Review output
- [ ] Decision journal entries appear unmodified in Swedish Weekly Review output
- [ ] `render_weekly_review(result, locale="sv")` does not alter `result` fields

---

### B13 — Unsupported Locale Regression Tests

**Status: OPEN**

After `sv` is enabled, existing unsupported-locale tests must still pass:

- [ ] `ensure_supported_locale("fr")` still raises `ValueError`
- [ ] `ensure_supported_locale("de")` still raises `ValueError`
- [ ] `render_weekly_review(result, locale="fr")` still raises `ValueError`
- [ ] All 14 Snapshot renderer functions still raise for `locale="fr"`

---

### B14 — Full Suite Green with sv Enabled

**Status: OPEN**

After all above criteria are satisfied and `sv` is added:

- [ ] `pytest` passes with zero failures (3108+ tests)
- [ ] `scripts/run_daily_brief_demo.sh` green
- [ ] `scripts/run_internal_v1_demo.sh` green
- [ ] `scripts/verify_release_candidate.sh` green (RC2 green)

---

## Non-Blocking Criteria

The following are desirable but may be deferred past initial `sv` activation.
Each deferred item must be documented as a known gap at activation time.

### N1 — Swedish User-Facing Usage Guide

A Swedish variant of the Atlas usage guide. Users are expected to interact
with Atlas in English (CLI flags, file formats, schema); a Swedish usage
guide is a convenience, not a safety requirement.

**Current status: Not started.**

### N2 — Swedish Investor Profile Field Labels

Swedish display labels for investor profile fields in rendered output.
Investor profile content is user-provided and not translated; this covers
only Atlas-generated field labels.

**Current status: Not started.**

### N3 — Swedish Company Facts Field Labels

Swedish display labels for company facts fields in rendered output.
Company facts content is user-provided and not translated; this covers
only Atlas-generated field labels.

**Current status: Not started.**

### N4 — Swedish CLI Demo Script

A variant of `scripts/run_internal_v1_demo.sh` that passes `locale="sv"` at
the Python API level and verifies Swedish output end-to-end.

**Current status: Not started.**

### N5 — Swedish Weekly Review Scope Notes Integration Test

A full end-to-end test with Swedish scope notes provided by the user, verifying
that Atlas-generated Swedish headings surround unmodified Swedish user content.

**Current status: Not started.**

---

## Current Status Summary (Sprint 248)

| Criterion | Status | Sprint Completed |
|-----------|--------|-----------------|
| B1 — Guardrail specification | **DONE** | 247 |
| B2 — Readiness checklist (this document) | **DONE** | 248 |
| B3 — Swedish string constants | **DONE** | 249 |
| B4 — Swedish renderer dispatch boundary | **DONE** | 250 |
| B5 — locale_support.py updated | **DONE** | 251 |
| B6 — Forbidden-category scan tests | **DONE** | 252 |
| B7 — Swedish heading output tests | **DONE** | 252 |
| B8 — Swedish label output tests | **DONE** | 252 |
| B9 — Swedish disclaimer output test | **DONE** | 252 |
| B10 — Swedish Snapshot CLI heading tests | **DONE** | 252 |
| B11 — Canonical value preservation tests | OPEN | — |
| B12 — User-provided content passthrough tests | OPEN | — |
| B13 — Unsupported locale regression tests | OPEN | — |
| B14 — Full suite green with sv enabled | OPEN | — |

**10 of 14 blocking criteria satisfied.**

`sv` is now supported in direct renderer calls. Swedish output is internally
tested through `tests/test_swedish_output_matrix_sprint252.py`. All 10 Weekly
Review section titles, all body labels, the two-line disclaimer, input status
templates, warning format, all 6 Snapshot headings, and all safety boundary
labels pass. Forbidden-category scan covers all 7 prohibited categories across
all rendered Swedish outputs. CLI output remains English — there is no
`--language` option and the CLI does not pass a locale. B11–B14 remain OPEN.

---

## How to Activate sv

When all blocking criteria above are DONE:

1. Add `SUPPORTED_LOCALE_SV = "sv"` to `atlas/locale_support.py`
2. Update `ensure_supported_locale` to accept `"sv"` without raising
3. Confirm all 14 blocking criteria tests pass
4. Update this document: change all OPEN → DONE with sprint numbers
5. Update `docs/AtlasLocalizationBoundary.md` with activation sprint
6. Update `docs/InternalV1ReleaseCandidate.md` and `docs/DecisionLog.md`

Do not activate `sv` by modifying only `locale_support.py`. The string constants
(B3) and renderer integration (B4) must exist first or calls to `locale="sv"` will
raise `KeyError` / `AttributeError` rather than producing Swedish output.

---

## Recommended Implementation Order

The blocking criteria are interdependent. The recommended sprint order:

| Sprint | Work |
|--------|------|
| Next | B3 — Create `atlas/weekly_review/strings_sv.py` with approved section titles and labels |
| +1 | B3 (cont.) — Create `atlas/snapshot_input/strings_sv.py` with Snapshot CLI headings |
| +2 | B4 — Wire Swedish dispatch into Weekly Review renderer |
| +3 | B4 (cont.) — Wire Swedish dispatch into Snapshot CLI renderers |
| +4 | B5 — Update `locale_support.py` to accept `"sv"` |
| +5 | B6–B9 — Forbidden-category scan and Weekly Review Swedish output tests |
| +6 | B10–B12 — Snapshot CLI, canonical value, and passthrough tests |
| +7 | B13–B14 — Regression tests, full suite, demos, activation |

This order ensures each sprint is a safe, testable increment: string constants
exist before renderer dispatch, renderer dispatch exists before locale activation.

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [docs/SwedishSafeLanguageGuardrails.md](SwedishSafeLanguageGuardrails.md) | Prohibited Swedish phrases and safe alternatives |
| [docs/AtlasLocalizationBoundary.md](AtlasLocalizationBoundary.md) | Localization boundary rules and phase plan |
| [docs/AtlasUserFacingStringsInventory.md](AtlasUserFacingStringsInventory.md) | Complete inventory of localizable strings |
| [docs/InternalV1ReleaseCandidate.md](InternalV1ReleaseCandidate.md) | v1 release candidate status |
| [docs/DecisionLog.md](DecisionLog.md) | Sprint-by-sprint decisions |
