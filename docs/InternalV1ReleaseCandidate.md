# Atlas Internal v1 Release Candidate

**Sprint:** 217
**Date:** 2026-07-03
**Version:** 0.1.0
**Release stage:** Internal v1 RC — Weekly Review

---

## What Is Atlas Internal v1

Atlas internal v1 is a CLI-first, local-only Weekly Investment Review workflow
for long-term investment reasoning.

It loads a local portfolio, watchlist, optional investor profile, optional
decision journal, optional company facts, optional financials, and optional
scope notes. It renders a deterministic 10-section Weekly Review that surfaces
portfolio context, watchlist state, open decisions, missing evidence,
follow-up questions, and reasons to wait.

It does not provide investment recommendations, valuation forecasts, market-timing
signals, live news, live market data, broker integrations, UI, AI-generated
conclusions, or Atlas Edge behavior.

Atlas supports better judgment. It does not replace it.

---

## Included Capabilities

| Capability | Sprint | Status |
|-----------|--------|--------|
| `atlas weekly-review` command | 211 | Current |
| Local portfolio input (positions and accounts formats) | 210 | Current |
| Local watchlist input (rich v1 format with status/evidence/questions) | 210 | Current |
| Optional investor profile (principles, constraints, risk tolerance, time horizon) | 210/213 | Current — rendered in Sections 5 and 6 |
| Optional decision journal (raw entries, entry count, follow-up triggers) | 212/213 | Current |
| Optional company facts directory (per-ticker JSON presence check) | 213 | Current |
| Optional financials directory (per-ticker CSV presence check) | 213 | Current |
| Optional scope notes (markdown preview, header-stripped) | 213 | Current |
| Deterministic input validation with structured warnings | 210 | Current |
| Deterministic warning rendering | 210 | Current |
| Section 1 — Review Scope | 211/212 | Current |
| Section 2 — Portfolio Context (weights, sectors, concentration notes) | 212 | Current |
| Section 3 — Watchlist Review (per-item status, evidence gaps, questions) | 212 | Current |
| Section 4 — Company Reviews Needing Attention (portfolio/watchlist overlap, visible holdings) | 212 | Current |
| Section 5 — Portfolio Fit and Suitability Notes (profile fields, structural observations) | 212/213 | Current — local-input-derived, not engine-wired |
| Section 6 — Risk and Principle Guardrails (principles, risk scores, sector concentration) | 212/213 | Current — local-input-derived, not engine-wired |
| Section 7 — Open Decisions (journal summaries, follow-up triggers, aging notes) | 212/214 | Current |
| Section 8 — Missing Evidence (watchlist gaps, per-ticker missing facts/financials) | 212/213 | Current |
| Section 9 — Follow-Up Questions (watchlist questions, journal triggers) | 212 | Current |
| Section 10 — Non-Actions / Reasons to Wait (always non-empty) | 212 | Current |
| Journal aging alerts (open entries older than 90 days, uses `as_of`) | 214 | Current |
| Weekly Review usage guide | 215 | Current |

---

## Excluded Capabilities (Intentionally Deferred)

The following are not part of internal v1. They are documented limitations,
not regressions.

- Live market data or live prices
- Live news or earnings release ingestion
- Broker synchronisation (Avanza, Nordnet, or any other)
- Automatic portfolio import from external sources
- Screenshot or image ingestion
- Automatic research import
- Company analysis engine wired into Section 4
- Suitability engine wired into Section 5
- Risk/principles engine wired into Section 6
- Numerical financial CSV analysis (presence check only)
- Background alerts or notifications
- Investment recommendations of any kind
- Valuation forecasts or analyst-style targets
- Market-timing signals
- User interface or dashboard
- Multilingual renderer output
- LLM or AI-generated conclusions
- External API calls beyond existing opt-in provider behavior
- Atlas Edge concepts, naming, or architecture

---

## Command Surface

**Minimal command (required inputs only):**

```bash
atlas weekly-review \
  --portfolio my_review/portfolio.json \
  --watchlist my_review/watchlist.json
```

**Full command (all optional inputs):**

```bash
atlas weekly-review \
  --portfolio my_review/portfolio.json \
  --watchlist my_review/watchlist.json \
  --profile my_review/investor_profile.json \
  --journal my_review/decision_journal.json \
  --company-facts my_review/company_facts \
  --financials my_review/financials \
  --as-of 2026-01-01 \
  --scope-notes my_review/scope_notes.md
```

See [docs/AtlasWeeklyReviewUsageGuide.md](AtlasWeeklyReviewUsageGuide.md) for
setup instructions, file format details, and output interpretation.

---

## Acceptance Criteria Checklist

All items must be met for internal v1 RC status.

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Repository identity confirmed as Atlas, not Atlas Edge | ✓ Met |
| 2 | `atlas weekly-review` command exists | ✓ Met |
| 3 | Minimal command exits 0 | ✓ Met |
| 4 | Full command exits 0 | ✓ Met |
| 5 | Realistic command exits 0 (if bundle exists) | ✓ Met |
| 6 | Local portfolio input loads (positions and accounts formats) | ✓ Met |
| 7 | Local watchlist input loads (rich v1 format) | ✓ Met |
| 8 | Optional inputs warn rather than fail | ✓ Met |
| 9 | All 10 sections render | ✓ Met |
| 10 | Section 10 is present and non-empty | ✓ Met |
| 11 | Output is deterministic with same inputs | ✓ Met |
| 12 | Journal aging uses `as_of`, not live clock | ✓ Met |
| 13 | Output avoids recommendation language | ✓ Met |
| 14 | Output avoids forecast/target language | ✓ Met |
| 15 | Output avoids action-pressure language | ✓ Met |
| 16 | Provider/network boundary is clean | ✓ Met |
| 17 | No broker integration introduced | ✓ Met |
| 18 | No live data dependency introduced | ✓ Met |
| 19 | Usage guide exists | ✓ Met |
| 20 | README points to usage guide | ✓ Met |
| 21 | Tests pass | ✓ Met — 3053 passed, 3 skipped |
| 22 | Demo passes | ✓ Met — RC2 green |
| 23 | Release verification passes | ✓ Met — RC2 green |
| 24 | Closed cleanup deletion targets remain absent | ✓ Met |

**Result: All 24 acceptance criteria met. Internal v1 RC status confirmed.**

---

## Guardrail Acceptance

| Guardrail | Status |
|-----------|--------|
| No investment recommendations in output | ✓ |
| No valuation forecasts or analyst-style targets in output | ✓ |
| No action-pressure language in output | ✓ |
| No market-timing claims in output | ✓ |
| No live provider dependency | ✓ |
| No Atlas Edge concepts | ✓ |
| Human judgment remains final | ✓ — "Atlas supports better judgment. It does not replace it." |
| No action warranted remains valid outcome | ✓ — Section 10 always states this explicitly |

Atlas Weekly Review v1 is a process support tool for investment reasoning
workflows. It is not investment advice. All output is derived from user-supplied
local files.

---

## Verification Results

| Check | Result |
|-------|--------|
| `python -m compileall atlas tests` | Clean — no errors |
| `pytest` | 1954 passed, 3 skipped |
| `scripts/verify_release_candidate.sh` | RC2 green |
| `scripts/run_daily_brief_demo.sh` | Green |
| `atlas weekly-review` minimal | Exit 0, all 10 sections |
| `atlas weekly-review` full | Exit 0, all 10 sections |
| `atlas weekly-review` realistic (with `--as-of 2026-01-01`) | Exit 0, all 10 sections, NESTE aging alert correct |

---

## Known Limitations

These are intentional deferred items for v1.1+:

1. Company analysis engine not wired into Section 4 — qualitative attention notes only
2. Suitability engine not wired into Section 5 — structural notes only
3. Risk/principles engine not wired into Section 6 — user-supplied data only
4. Financial CSV files not numerically analysed — presence check only
5. Profile principles/constraints not rule-checked against holdings
6. No live data of any kind
7. No multilingual output
8. No UI

---

## Defining Documents

| Document | Purpose |
|----------|---------|
| [docs/AtlasV1OperatingMode.md](AtlasV1OperatingMode.md) | v1 product boundary definition |
| [docs/AtlasWeeklyInvestmentReviewSpec.md](AtlasWeeklyInvestmentReviewSpec.md) | Full workflow specification |
| [docs/AtlasWeeklyReviewUsageGuide.md](AtlasWeeklyReviewUsageGuide.md) | v1 user-facing usage guide |
| [docs/WeeklyReviewReleaseHardening.md](WeeklyReviewReleaseHardening.md) | Sprint 216 hardening record |
| [docs/DecisionLog.md](DecisionLog.md) | Sprint-by-sprint decision record |

---

## Productization Track Summary

| Sprint | Milestone |
|--------|-----------|
| 208 | Atlas v1 operating mode defined |
| 209 | Weekly Investment Review specified |
| 210 | Local input schemas implemented |
| 211 | `atlas weekly-review` CLI command added |
| 212 | Deterministic renderer implemented |
| 213 | Realistic portfolio trial run |
| 214 | Journal aging alerts added |
| 215 | v1 usage guide created |
| 216 | Release hardening checkpoint |
| 217 | Internal v1 RC freeze |

---

## After the Freeze

The internal v1 RC baseline is now established. Further product expansion should
build on this foundation without changing the local-only, deterministic, provider-free
character of the Weekly Review workflow.

**Sprint 218 (post-v1 improvement — complete):**
Investor profile principles and constraints are now rendered in Sections 5, 6,
and 10. Each principle appears as a "Reason to Wait" in Section 10; each
constraint appears as a "No Action Warranted" note. Malformed fields warn and
fail safely. No suitability scoring, no engine wiring, no provider dependency.

**Sprint 219 (post-v1 improvement — complete):**
Per-ticker local evidence presence checks added. `WeeklyReviewTickerEvidence`
dataclass tracks presence and source for each investable ticker. Section 8 emits
per-ticker `Evidence Gap [TICKER]` lines. Section 9 adds per-ticker follow-up
questions. Section 10 adds per-ticker reasons to wait. No provider dependency.

**Sprint 220 (post-v1 improvement — complete):**
Second realistic trial run. Four verbosity problems found and fixed: Section 8
combined "both missing" into one line per ticker; Section 9 replaced 24 identical
per-ticker questions with two grouped lists; Section 10 consolidated 24 per-ticker
reasons into two summary lines and collapsed principle/constraint boilerplate into
blocks. Section 10 reduced from ~40 to ~18 lines.

**Sprint 221 (post-v1 specification — complete):**
Snapshot / Screenshot Input workflow specified. New document
`docs/AtlasSnapshotInputWorkflow.md` defines seven snapshot types (Portfolio,
Watchlist, Open Orders, News, External Analysis, Research Notes, Company Facts),
a classification contract, a draft contract with five confirmation states, accuracy
and safety guardrails, a privacy and security boundary, mapping from each snapshot
type to existing Atlas local input files, and relationship to future chat-first
workspace UX. No runtime behavior changed. No OCR, AI, image parsing, or provider
dependency introduced. Internal v1 foundation unchanged.

**Sprint 222 (post-v1 improvement — complete):**
Research notes input added to Weekly Review. New `--research-notes DIR` CLI
argument. Per-ticker `research_notes/<TICKER>/notes.md` files are loaded with
bounded reads and lightweight section parsing. Evidence gaps surface in Section 8;
open questions and risks in Section 9; reasons to wait in Section 10. Missing or
malformed notes are non-blocking. Two example files added. No OCR, AI, image
parsing, or provider dependency introduced. Internal v1 foundation unchanged.

**Sprint 223 (post-v1 improvement — complete):**
Snapshot Draft schema defined. New `atlas/snapshot_input/` package. `SnapshotType`
(8 values), `SnapshotConfirmationStatus` (5 states), `SnapshotConfidence` (4 levels),
`SnapshotDraft` dataclass with validation, serialization (`to_dict`/`from_dict`/
`to_json`/`from_json`), and file helpers (`load_snapshot_draft`/`save_snapshot_draft`).
Three example draft files. No OCR, AI, or provider dependency. No Weekly Review
behavior changed. Internal v1 foundation unchanged.

**Sprint 227 (post-v1 specification — complete):**
Snapshot Draft confirmation workflow defined. New document
`docs/SnapshotDraftConfirmationWorkflow.md`. Specifies 11 confirmation principles,
all five state definitions, exportability rule, review checklist, blocking rules,
field correction model, future CLI shapes (`review`, `confirm`, `reject`,
`supersede`), export dependency, audit/traceability expectations, and safety
boundary. No runtime behavior changed. No new CLI commands. Internal v1 foundation
unchanged.

**Sprint 226 (post-v1 validation — complete):**
Third real portfolio trial with exported research notes. Full end-to-end loop
validated: confirmed draft → `snapshot validate` → `export-research-notes` →
`weekly-review --research-notes DIR` → Sections 8, 9, 10. Three tickers (ASML,
XYL, NOVO) tested in both example and realistic bundles. Loop confirmed functional,
useful, and safe. No code changes. Two additional confirmed draft examples added.
Trial findings documented. Internal v1 foundation unchanged.

**Sprint 225 (post-v1 improvement — complete):**
`atlas snapshot export-research-notes` added — the first safe Snapshot Draft
conversion path. Converts a confirmed `research_notes_snapshot` draft to a local
`research_notes/<TICKER>/notes.md` file. Enforces: type, confirmation status,
safe ticker, overwrite guard. Bounded output (500 chars/bullet, 20/section).
Draft never mutated. End-to-end path confirmed: exported notes.md immediately
readable by Weekly Review `--research-notes DIR`. No provider imports. No network
calls. No OCR. No AI. No Weekly Review behavior changed. Internal v1 foundation
unchanged.

**Sprint 246 (post-v1 architecture — complete):**
Shared locale boundary helper created. `atlas/locale_support.py` provides `SUPPORTED_LOCALE_EN = "en"` and `ensure_supported_locale(locale: str) -> None`. `atlas/weekly_review/render.py` and `atlas/snapshot_input/render.py` both import and use the shared helper; local duplicate guards removed. Error message preserved exactly. Sprint 244 and Sprint 245 tests updated to accept shared-helper pattern. 31 new tests (3053 total). All demos green. RC2 green.

**Sprint 245 (post-v1 architecture — complete):**
Snapshot CLI locale boundary defined. All 14 public renderer functions in `atlas/snapshot_input/render.py` now accept `*, locale: str = "en"`. Shared `_ensure_locale(locale)` helper and `_SUPPORTED_LOCALE = "en"` constant added. Unsupported locales raise `ValueError`. CLI unchanged — no `--language`, no `locale=` call sites. Sprint 244 test updated to reflect Snapshot renderer now has locale parameter (boundary was correct — cross-module imports still absent). 38 new tests (3022 total). All demos green. RC2 green.

**Sprint 255 (post-v1 architecture — complete):**
Dedicated sv activation full-suite gate created. `tests/test_sv_activation_full_suite_gate_sprint255.py` — compact release gate verifying all 14 Swedish readiness criteria hold together. Coverage: B1–B14 all DONE in checklist, "14 of 14" satisfied, all 8 prior Swedish test files present (`test_swedish_safe_language_guardrails_sprint247.py` through `test_unsupported_locale_regression_sprint254.py`), `_SUPPORTED_LOCALES == frozenset({"en", "sv"})`, `ensure_supported_locale` accepts en/sv and rejects fr/en-US/sv-SE, direct Swedish rendering smoke tests (title, section title, disclaimer, Snapshot review/validation headings, `Säkerhetsgräns`), English/CLI preservation (default output, explicit en, CLI weekly-review, CLI snapshot validate, `--help` no `--language`, CLI source no `locale="sv"`), safety infrastructure (no gettext imports, no locale detection, no translation catalogs, no provider imports, no extra supported locales in source). No production code changes. Swedish internal activation is complete. Swedish remains direct-renderer/internal only — CLI remains English. Any future CLI exposure requires a separate planning sprint. 14 of 14 blocking criteria satisfied. B14 is DONE. Tests added. All demos green. RC2 green.

**Sprint 254 (post-v1 architecture — complete):**
Unsupported-locale regression matrix created. `tests/test_unsupported_locale_regression_sprint254.py` — systematic regression matrix covering the full locale-aware renderer surface. 13 unsupported locale values verified to raise `ValueError`: `fr`, `de`, `ja`, `no`, `da`, `fi`, `es`, `xx`, `""`, `EN`, `SV`, `en-US`, `sv-SE`. Coverage: `ensure_supported_locale` (13 values each), `render_weekly_review` (13 values), all 14 public Snapshot locale-aware renderer functions (6 values each for most). Error message quality verified: unsupported locale named in message, supported locales listed. `_SUPPORTED_LOCALES` verified exactly `frozenset({"en", "sv"})`. No other language code present in `locale_support.py` as supported. `en` and `sv` verified still passing in all renderer functions. CLI remains English — no `--language`. No production code changes. No locale_support.py changes. No renderer changes. Readiness checklist B13 marked DONE (13 of 14 criteria satisfied). B14 remains OPEN. Tests added. All demos green. RC2 green.

**Sprint 253 (post-v1 architecture — complete):**
Swedish canonical value and user-content passthrough matrix created. `tests/test_swedish_canonical_passthrough_sprint253.py` — systematic matrix covering B11 and B12. All 8 SnapshotType values (`research_notes_snapshot`, `company_facts_snapshot`, `portfolio_snapshot`, `watchlist_snapshot`, `open_orders_snapshot`, `news_snapshot`, `external_analysis_snapshot`, `unknown_snapshot`) verified unchanged in Swedish renderer output. All 5 SnapshotConfirmationStatus values (`draft`, `needs_user_review`, `confirmed`, `rejected`, `superseded`) verified unchanged. All 4 SnapshotConfidence values (`high`, `medium`, `low`, `unknown`) verified unchanged. Warning codes verified unchanged; warning code format (`[{code}]`) verified canonical; en/sv warning code parity verified. Ticker symbols (`MSFT`, `ASML`, `CASH`, `XYL`, `NOVO`) verified unchanged. File paths (`target_local_file`, `raw_source_reference`) verified unchanged. User-provided scope notes (Swedish and English), watchlist reasons, research note text, journal `decision_title`, snapshot `notes`, `source_description`, and extracted field values all verified unchanged in Swedish output. `render_weekly_review(result, locale="sv")` verified not to mutate `result` fields. Render verified idempotent. English output verified identical before and after calling the Swedish renderer. No locale_support.py changes. No renderer changes. No string module changes. CLI output unchanged. Readiness checklist B11 and B12 marked DONE (12 of 14 criteria satisfied). B13 and B14 remain OPEN. Tests added. All demos green. RC2 green.

**Sprint 252 (post-v1 architecture — complete):**
Swedish output test matrix created. `tests/test_swedish_output_matrix_sprint252.py` — 91 tests covering: B7 (all 10 Weekly Review section titles in Swedish), B8 (all body labels, input status templates, warning format), B9 (Swedish disclaimer both lines, English disclaimer absent), B10 (all 6 Snapshot CLI headings, safety boundary labels, Swedish status lines), B6 (forbidden-category scan across all 7 prohibited categories on full rendered Swedish output from all direct renderer calls). Canonical value preservation spot-checked (warning codes, ticker symbols, file paths, snapshot types, confirmation statuses). User content passthrough spot-checked (scope notes, watchlist reasons, research note evidence gaps, journal notes, snapshot source reference). CLI English preservation verified. Renderer bug fixed: two hardcoded English phrases in Weekly Review section 10 now use locale dispatch via `S.REMINDER_NO_ACTION_VALID` and `S.REMINDER_ATLAS_SUPPORTS_JUDGMENT` — `REMINDER_NO_ACTION_VALID` and `REMINDER_ATLAS_SUPPORTS_JUDGMENT` added to both `strings.py` and `strings_sv.py`. English constants are identical to previous hardcoded strings. No CLI changes. No schema changes. Readiness checklist B6–B10 marked DONE (10 of 14 criteria satisfied). B11–B14 remain OPEN. 91 new tests (3443 total). All demos green. RC2 green.

**Sprint 251 (post-v1 architecture — complete):**
sv locale activated internally without CLI exposure. `atlas/locale_support.py` updated: `SUPPORTED_LOCALE_SV = "sv"` constant added, `_SUPPORTED_LOCALES = frozenset({"en", "sv"})` internal set added, `ensure_supported_locale` now checks `locale not in _SUPPORTED_LOCALES`, error message updated to `"Supported locales: 'en', 'sv'."`. `ensure_supported_locale("sv")` now passes. `ensure_supported_locale("fr")` still raises. `render_weekly_review(result, locale="sv")` produces Swedish display strings (title, all 10 section headings, labels). All 14 Snapshot renderer functions return Swedish display strings for `locale="sv"`. Default locale unchanged (`"en"`). CLI output remains English — no `--language` option, CLI does not pass locale. No gettext. No string catalogs. No locale detection. No schemas changed. No enum values changed. Tests from sprints 244–250 updated to use `"fr"` as the unsupported-locale test value where they previously used `"sv"`. Readiness checklist B5 marked DONE (5 of 14 criteria satisfied). B6–B14 remain OPEN. sv is now supported only in direct renderer calls. 47 new tests (3352 total). All demos green. RC2 green.

**Sprint 250 (post-v1 architecture — complete):**
Swedish renderer dispatch boundary defined. `_strings_for_locale(locale)` dispatch helper added to both `atlas/weekly_review/render.py` and `atlas/snapshot_input/render.py`. Helpers call `ensure_supported_locale(locale)` unconditionally; map `"en"` to English constants (default); map `"sv"` to Swedish constants (unreachable until B5). Weekly Review renderer refactored: `strings` import renamed to `strings_en`, `strings_sv` imported, module-level `_TITLE` constant removed, `S` now a local variable set per render call, all section helpers and `_render_journal_aging_note` take `S` as parameter. Snapshot CLI renderer: all 14 public functions call `S = _strings_for_locale(locale)` instead of `_ensure_locale(locale)`. Default English output unchanged. `render_weekly_review(result, locale="sv")` and all 14 Snapshot functions still raise `ValueError`. No new CLI options. No gettext. `atlas/locale_support.py` unchanged. Readiness checklist B4 marked DONE (4 of 14 criteria satisfied). 37 new tests (3303 total). All demos green. RC2 green.

**Sprint 249 (post-v1 architecture — complete):**
Swedish display string constants defined. `atlas/weekly_review/strings_sv.py` created with `WEEKLY_REVIEW_TITLE`, all 10 section titles, `WEEKLY_REVIEW_SECTION_TITLES` tuple, 7 body labels, 2 section headings, 14 `INPUT_STATUS_*` templates, warning templates, and `WEEKLY_REVIEW_DISCLAIMER`. `atlas/snapshot_input/strings_sv.py` created with all 6 command headings, 7 status lines, 3 exportability lines, 9 section headers, 12 safety boundary lines, and 3 confirm/reject note lines. Neither module imported by active renderers. All Swedish wording follows `docs/SwedishSafeLanguageGuardrails.md`. No canonical values translated. No renderer dispatch added. `sv` not enabled. `atlas/locale_support.py` unchanged. Runtime output English. Readiness checklist B3 marked DONE (3 of 14 criteria satisfied). 94 new tests (3266 total). All demos green. RC2 green.

**Sprint 248 (post-v1 architecture — complete):**
Swedish localization readiness checklist created. `docs/SwedishLocalizationReadinessChecklist.md` defines 14 blocking criteria (B1–B14) and 5 non-blocking criteria (N1–N5) that must be satisfied before `sv` is enabled. B1 (guardrail spec, Sprint 247) and B2 (this checklist) are DONE. B3–B14 are OPEN. Current status: 2 of 14 blocking criteria satisfied. Includes how-to-activate instructions, recommended implementation order across future sprints, and status table. `sv` not enabled. `atlas/locale_support.py` unchanged. No renderer changes. No translations. 64 new tests (3172 total). All demos green. RC2 green.

**Sprint 247 (post-v1 architecture — complete):**
Swedish safe-language guardrail specification created. `docs/SwedishSafeLanguageGuardrails.md` defines all safety requirements that must be satisfied before Atlas may generate Swedish-language output. Documents 7 prohibited Swedish language categories (recommendation, transaction, price-target, urgency, certainty, outperformance, personalized advice) with guardrail-context-only examples. Provides safe Swedish alternative table (~25 entries), Atlas concept mapping for Weekly Review and Snapshot CLI, 10 Swedish Weekly Review style rules, 6 Swedish Snapshot CLI style rules, user-provided content handling rules, guardrail-sensitive phrase table, and 10 testing requirements before `sv` can be enabled. `sv` is not enabled. `atlas/locale_support.py` unchanged. No renderer changes. No translations. No gettext. No `--language`. 55 new tests (3108 total). All demos green. RC2 green.

**Sprint 246 (post-v1 architecture — complete):**
Shared locale boundary helper centralized. `atlas/locale_support.py` created with `SUPPORTED_LOCALE_EN = "en"` and `ensure_supported_locale(locale: str) -> None`. Both `atlas/weekly_review/render.py` and `atlas/snapshot_input/render.py` now import and call the shared helper. Local duplicate `_SUPPORTED_LOCALE` and `def _ensure_locale` removed from both modules. Snapshot render uses aliased import (`ensure_supported_locale as _ensure_locale`) preserving all 14 existing call sites verbatim. Error message unchanged. No output changed. 31 new tests (3053 total). All demos green. RC2 green.

**Sprint 245 (post-v1 architecture — complete):**
Snapshot CLI locale boundary defined. All 14 public Snapshot CLI renderer functions in `atlas/snapshot_input/render.py` now accept `*, locale: str = "en"`. A shared `_ensure_locale(locale)` helper and `_SUPPORTED_LOCALE = "en"` constant guard each function. Unsupported locales raise `ValueError`. Default behavior and all output unchanged. CLI unchanged. No `--language`. No translations. 38 new tests (3022 total). All demos green. RC2 green.

**Sprint 244 (post-v1 architecture — complete):**
Weekly Review locale boundary defined. `render_weekly_review(result, *, locale: str = "en") -> str` now accepts an explicit keyword-only `locale` parameter. Only `"en"` is currently supported; unsupported locales raise `ValueError`. Default output and all CLI behavior unchanged. No `--language` added. No translations, gettext, or locale detection introduced. No locale files created. `docs/AtlasLocalizationBoundary.md` updated with boundary definition and usage examples. 30 new tests (2984 total). All demos green. RC2 green.

**Sprint 243 (post-v1 architecture — complete):**
Weekly Review warning display templates extracted to constants. `atlas/weekly_review/strings.py` extended with `WARNING_ROW = "- [{code}] {message}"` and `WARNING_SCOPE_SUMMARY = "Warnings: {count} input warning(s) noted — see Input Warnings section"`. `_render_warnings` and `_section1_scope` in `render.py` updated to reference constants. Warning codes remain canonical internal values in `inputs.py`. Warning messages remain inline (embed dynamic file paths). Warning row format `- [missing_optional_profile] ...` verified unchanged. No `--language` added. No locale imports. No output changed. 30 new tests (2954 total). All demos green. RC2 green.

**Sprint 242 (post-v1 architecture — complete):**
Weekly Review input status message templates extracted to constants. `atlas/weekly_review/strings.py` extended with 14 `INPUT_STATUS_*` constants covering all `_render_input_status` output lines. `atlas/weekly_review/render.py` `_render_input_status` updated to reference all constants via `.format(...)` or direct reference. Inline f-string literals removed from status function. Both full-input (available paths) and minimal-input (not-provided paths) output verified unchanged. Warning body prose remains inline. No `--language` added. No locale imports. No output changed. 52 new tests (2924 total). All demos green. RC2 green.

**Sprint 241 (post-v1 architecture — complete):**
Weekly Review disclaimer extracted to constants. `atlas/weekly_review/strings.py` extended with `WEEKLY_REVIEW_DISCLAIMER` — the two-line guardrail disclaimer. Inline `_DISCLAIMER` module-level variable removed from `atlas/weekly_review/render.py`; renderer now references `S.WEEKLY_REVIEW_DISCLAIMER`. Disclaimer wording, punctuation, and line break preserved exactly. No `--language` added. No locale imports. No output changed. 25 new tests (2872 total). All demos green. RC2 green.

**Sprint 240 (post-v1 architecture — complete):**
Weekly Review section body labels extracted to constants. `atlas/weekly_review/strings.py` extended with 9 label constants: `LABEL_EVIDENCE_GAP`, `LABEL_RISK_TO_MONITOR`, `LABEL_REASON_TO_WAIT`, `LABEL_DECISION_DEFERRED`, `LABEL_NO_ACTION_WARRANTED`, `LABEL_AGING_NOTE`, `LABEL_MISSING_OPTIONAL_INPUT`, `LABEL_INPUT_STATUS`, `LABEL_INPUT_WARNINGS`. `atlas/weekly_review/render.py` updated with ~20 targeted replacements across sections 3, 6, 8, 9, 10, `_render_journal_aging_note`, `_render_input_status`, `_render_warnings`. Enum values, user passthrough content, and `_DISCLAIMER` remain inline. No `--language` added. No locale imports. No output changed. 38 new tests (2847 total). All demos green. RC2 green.

**Sprint 239 (post-v1 architecture — complete):**
Weekly Review section titles extracted to constants. New `atlas/weekly_review/strings.py` contains `WEEKLY_REVIEW_TITLE`, 10 section title constants (`SECTION_REVIEW_SCOPE` through `SECTION_NON_ACTIONS_REASONS_TO_WAIT`), and `WEEKLY_REVIEW_SECTION_TITLES` ordered tuple. `atlas/weekly_review/render.py` updated to import `strings as S` and reference all section title constants. Inline title literals removed from renderer. All 10 section headings verified byte-for-byte identical after refactor. No `--language` added. No locale imports. No output changed. 38 new tests. Snapshot CLI strings unaffected.

**Sprint 238 (post-v1 architecture — complete):**
Snapshot CLI display strings extracted to constants. New `atlas/snapshot_input/strings.py` contains 6 command headings, 7 status display lines, exportability lines, 9 section header labels, 12 safety boundary lines, and 3 confirm/reject note lines. `atlas/snapshot_input/render.py` updated to import and reference all constants via `from atlas.snapshot_input import strings as S`. All 6 representative CLI commands verified byte-for-byte unchanged. Canonical enum values (`confirmed`, `rejected`, `research_notes_snapshot`, etc.) did not move — they remain in schema enums. Weekly Review renderer untouched. No `--language` option added. No locale imports added. No output changed. 64 new tests. Sprint 239 recommendation: extract Weekly Review section titles into constants.

**Sprint 237 (post-v1 architecture — complete):**
User-facing strings inventory extracted. `docs/AtlasUserFacingStringsInventory.md` catalogs all Atlas-generated display strings across the Weekly Review renderer (~90 string groups, 10 sections) and Snapshot CLI renderer (~50 string groups, 6 commands). Classifies each as `localizable_display`, `canonical_internal`, `user_content_passthrough`, `command_or_file_convention`, or `guardrail_sensitive_display`. Identifies Section 10 as highest-density guardrail-sensitive section. Identifies Safety Boundary text as highest-risk localization target. Inventories 17 distinct user-provided content passthrough contexts. Documents all canonical internal enum values, CLI option names, schema keys, and file conventions that must never be localized. Recommends extracting Snapshot CLI strings as the lowest-risk Phase 2 starting point. 49 new tests. No runtime behavior changed. No strings moved. Internal v1 foundation unchanged.

**Sprint 236 (post-v1 architecture — complete):**
Localization boundary defined. `docs/AtlasLocalizationBoundary.md` specifies which Atlas strings are permanent canonical English (enum values, schema keys, CLI option names, file conventions, test fixture keys) and which are localizable display text (rendered CLI output, Weekly Review section titles, explanatory text). Documents 10 boundary rules, locale-specific guardrail requirements, user-provided content handling, Snapshot Draft boundary table, Weekly Review boundary table, documentation boundary, 6-phase future implementation plan, and explicit out-of-scope list. 28 new tests verify document completeness and confirm no runtime behavior or enum values changed. No `--language` option added. No multilingual rendering implemented. Internal v1 foundation unchanged.

**Sprint 235 (post-v1 packaging — complete):**
Internal v1 demo package created. `docs/InternalV1DemoPackage.md` documents the complete safe user journey across 7 stages: snapshot draft validate, review, confirm, reject, export-research-notes, export-company-facts, and weekly-review. `scripts/run_internal_v1_demo.sh` runs all 7 stages end-to-end, writes only to `/tmp/atlas_internal_v1_demo/`, verifies output file presence and that rejected drafts are blocked from export, and cleans up after itself. 23 new tests verify doc completeness, script safety, command coverage, and language guardrails. No runtime behavior changed. No new commands added. Internal v1 foundation unchanged.

**Sprint 234 (post-v1 validation — complete):**
Sixth real portfolio trial — company facts export loop. Full chain confirmed green: `validate` (valid, confirmed) → `review` (Exportable: yes) → `export-company-facts` (ASML.json written, draft MD5 unchanged) → `weekly-review --company-facts DIR` (Section 8 clears ASML, MSFT/NOVO/XYL remain; Section 9 lists tickers without facts by name; Section 10 narrows reason-to-wait to named tickers). Mutation safety verified. Language guardrails clean. No code changes. Findings documented in `docs/SnapshotCompanyFactsExportTrialFindings.md`. Internal v1 foundation unchanged.

**Sprint 233 (post-v1 improvement — complete):**
`atlas snapshot export-company-facts <path> --output-dir DIR` added — the second safe Snapshot Draft conversion path. Converts a confirmed `company_facts_snapshot` draft to a local `<TICKER>.json` file under the output directory. Enforces: type (`company_facts_snapshot` only), confirmation status (`confirmed` only), safe ticker, overwrite guard. Bounded output (800 chars/string, 30 list items, 500 chars/item). Draft never mutated. No portfolio, watchlist, journal, or research notes files written. Source provenance (`draft_id`, `source_description`) written into `source` key. Output detected by `atlas weekly-review --company-facts DIR`. No OCR. No AI. No provider imports. No network calls. Internal v1 foundation unchanged.

**Sprint 232 (post-v1 validation — complete):**
Fifth real portfolio trial — confirm and reject branch validation. Both branches
green. Confirm branch: `confirm` → `validate` → `review` (Exportable: yes) →
`export-research-notes` → `weekly-review` (Sections 8/9/10 correct). Reject branch:
`reject` → `validate` → `review` (Exportable: no) → `export-research-notes` blocked
(exit 1, no directory created). MD5 verified original draft unchanged throughout.
Safety boundaries correct and distinct per command. No code changes. Findings
documented in `docs/SnapshotStatusWorkflowTrialFindings.md`. Internal v1 foundation
unchanged.

**Sprint 231 (post-v1 improvement — complete):**
`atlas snapshot reject <path> --output-draft <path>` CLI command added. Writes a
rejected draft copy (`confirmation_status: rejected`) without mutating the original
draft or any Atlas local input files. `draft`, `needs_user_review`, `confirmed`,
and `rejected` states produce a rejected copy. `superseded` is hard-blocked.
Confirmed and already-rejected inputs produce copies with informational notes.
Output path must differ from input path. Default: refuse to overwrite; `--overwrite`
enables replacement. `export-research-notes` blocks rejected copies. No OCR. No AI.
No provider imports. Internal v1 foundation unchanged.

**Sprint 230 (post-v1 validation — complete):**
Fourth real portfolio trial — full review-confirm-export-Weekly Review loop. Full
chain confirmed green: `review` (draft, Exportable: no) → `confirm` (original
unchanged, MD5 verified) → `validate` (confirmed copy valid) → `review` (confirmed
copy, Exportable: yes) → `export-research-notes` (ASML/notes.md written) →
`weekly-review` (Sections 8/9/10 surface ASML research notes with provenance
labels). Both example and realistic bundles pass. No code changes. Trial findings
documented in `docs/SnapshotConfirmExportTrialFindings.md`. Internal v1 foundation
unchanged.

**Sprint 229 (post-v1 improvement — complete):**
`atlas snapshot confirm <path> --output-draft <path>` CLI command added. Loads a
Snapshot Draft, applies Sprint 227/228 blocking rules, and writes a new confirmed
draft copy. `draft` and `needs_user_review` states confirm if no blocking issues.
`confirmed` input writes a confirmed copy with a note. `rejected` and `superseded`
are hard-blocked. Output path must differ from input path (no in-place confirmation).
Default: refuse to overwrite existing output; `--overwrite` enables replacement.
Original draft is never mutated. No Atlas local input files written. No OCR. No AI.
No provider imports. End-to-end chain confirmed: review → confirm → validate →
review (Exportable: yes) → export-research-notes. Internal v1 foundation unchanged.

**Sprint 228 (post-v1 improvement — complete):**
`atlas snapshot review <path>` CLI command added. Read-only confirmation checklist
for a Snapshot Draft. Renders: snapshot type, confidence, confirmation status,
exportability (yes/no with reason), source, extracted fields summary (bounded,
no unbounded output), uncertainties, missing required fields, blocking issues per
Sprint 227 rules, research-notes-specific section for `research_notes_snapshot`,
and safety boundary. Exit 0 on valid draft, exit 1 on missing file, invalid JSON,
or invalid schema. Does not confirm, reject, or write any file. No provider imports.
No network calls. No Weekly Review behavior changed. Internal v1 foundation unchanged.

**Sprint 224 (post-v1 improvement — complete):**
`atlas snapshot validate <path>` CLI command added. Validates a Snapshot Draft JSON
file and renders a human-readable summary: type, confidence, confirmation status,
target local file, related tickers, uncertainties, missing required fields, and
safety boundary. Exit 0 on valid, exit 1 on invalid JSON, invalid schema, or missing
file. No file writing. No mutation. New `atlas/snapshot_input/render.py`. CLI extended
with `snapshot_app` Typer sub-group. No provider imports. No network calls. No
Weekly Review behavior changed. Internal v1 foundation unchanged.
