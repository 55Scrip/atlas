# Atlas User-Facing Strings Inventory

**Sprint:** 237 (inventory) / 238 (Snapshot CLI extraction) / 239 (Weekly Review section titles) / 240 (Weekly Review section labels) / 241 (Weekly Review disclaimer) / 242 (Weekly Review input status messages) / 243 (Weekly Review warning display templates) / 262 (Weekly Review body message templates) / 263 (Weekly Review Section 10 tail messages) / 264 (Section 6/8 input-status tail messages)
**Date:** 2026-07-04
**Status:** Snapshot CLI strings extracted / Weekly Review section titles extracted / Weekly Review section labels extracted / Weekly Review disclaimer extracted / Weekly Review input status messages extracted / Weekly Review warning display templates extracted / Weekly Review body message templates extracted (Sprint 262) / Section 10 tail messages extracted (Sprint 263) / Section 6/8 input-status tail messages extracted (Sprint 264)

---

## Purpose

This document inventories all Atlas-generated user-facing display strings across
the Weekly Review renderer, Snapshot CLI renderer, and CLI help/output. It
classifies each string group as localizable display text, canonical internal
value, user-provided passthrough, or other category. This is Phase 1 of the
localization plan from `docs/AtlasLocalizationBoundary.md`.

Sprint 237: No strings moved. Audit only.
Sprint 238: Snapshot CLI display strings extracted to `atlas/snapshot_input/strings.py`.
Sprint 239: Weekly Review section titles extracted to `atlas/weekly_review/strings.py`.
Sprint 240: Weekly Review section labels extracted to `atlas/weekly_review/strings.py` — `LABEL_EVIDENCE_GAP`, `LABEL_RISK_TO_MONITOR`, `LABEL_REASON_TO_WAIT`, `LABEL_DECISION_DEFERRED`, `LABEL_NO_ACTION_WARRANTED`, `LABEL_AGING_NOTE`, `LABEL_MISSING_OPTIONAL_INPUT`, `LABEL_INPUT_STATUS`, `LABEL_INPUT_WARNINGS`.
Sprint 241: Weekly Review disclaimer extracted to `atlas/weekly_review/strings.py` as `WEEKLY_REVIEW_DISCLAIMER`. Inline `_DISCLAIMER` module-level assignment removed from `render.py`. Wording unchanged.
Sprint 242: Weekly Review input status message templates extracted
Sprint 243: Weekly Review warning display templates extracted to `atlas/weekly_review/strings.py` as `WARNING_ROW = "- [{code}] {message}"` and `WARNING_SCOPE_SUMMARY = "Warnings: {count} input warning(s) noted — see Input Warnings section"`. Warning codes remain canonical internal values and are not extracted. Warning messages in `inputs.py` remain inline (embed dynamic file paths). Renders `_render_warnings` and section 1 scope function updated to reference constants. to `atlas/weekly_review/strings.py` — 14 constants covering all `_render_input_status` output lines (portfolio loaded, watchlist loaded, investor profile available/not-provided, decision journal loaded/not-provided, company facts available/not-provided, financials available/not-provided, research notes loaded/not-provided, review date, warnings count). Warning body prose remains inline.
Sprint 262: Weekly Review section body message templates extracted — 27 constants covering Sections 1–9 body messages (scope mode/summaries, portfolio headers/note, watchlist/attention/suitability/guardrails/decisions/evidence/questions fallback and fixed messages). Matching Swedish constants added to `strings_sv.py`. `_section2_portfolio`, `_section4_attention`, and `_section5_suitability` updated to accept `S` parameter. Section 6 guardrails check updated to use locale-correct label values (fixing a latent Swedish bug). English output unchanged. Swedish output now fully uses Swedish body message constants.
Sprint 263: Weekly Review Section 10 tail messages extracted — 12 constants (`NONACTIONS_WAIT_*`, `NONACTIONS_NO_ACTION_*`) covering all hardcoded English tail suffixes in `_section10_nonactions`: evidence gaps, no-profile, no-journal, missing facts/fins (per-ticker), no company facts/financials loaded (directory absent), aging journal tail, research notes gaps, stated principles intro, stated constraints intro, and informational-only universal reminder. Matching Swedish constants added to `strings_sv.py`. English output unchanged. Swedish Section 10 now fully uses Swedish tail constants.
Sprint 264: Section 6/8 input-status tail messages extracted — 6 constants covering the last hardcoded English strings visible in Swedish output: `GUARDRAILS_EVIDENCE_NO_COMPANY_FACTS` and `GUARDRAILS_EVIDENCE_NO_FINANCIALS` (Section 6 `_section6_guardrails` evidence-gap tails); `EVIDENCE_MISSING_PROFILE`, `EVIDENCE_MISSING_JOURNAL`, `EVIDENCE_MISSING_COMPANY_FACTS`, `EVIDENCE_MISSING_FINANCIALS` (Section 8 `_section8_evidence` missing-optional-input tails). Matching Swedish constants added to `strings_sv.py`. English output unchanged. Swedish Sections 6 and 8 no longer leak extracted English strings.

---

## Scope

Files inspected:

| File | Role |
|------|------|
| `atlas/weekly_review/render.py` | Weekly Review renderer (917 lines) |
| `atlas/snapshot_input/render.py` | Snapshot CLI renderer (453 lines) |
| `atlas/cli/main.py` | CLI command definitions (1971 lines) |
| `atlas/snapshot_input/export.py` | Research notes export (233 lines) |
| `atlas/snapshot_input/export_company_facts.py` | Company facts export (225 lines) |
| `atlas/snapshot_input/confirm.py` | Confirm logic (149 lines) |
| `atlas/snapshot_input/reject.py` | Reject logic (140 lines) |
| `scripts/run_internal_v1_demo.sh` | Demo script |

---

## Classification Rules

| Category | Definition |
|----------|-----------|
| `localizable_display` | Atlas-generated text shown to the user that may later be translated |
| `canonical_internal` | Enum values, schema values, status values, or identifiers that must remain English |
| `user_content_passthrough` | User-supplied notes, fields, or draft content shown as-is |
| `command_or_file_convention` | CLI flags, command names, file paths, directory naming rules |
| `test_or_example_content` | Fixture or sample content used for tests or demos |
| `guardrail_sensitive_display` | Atlas-generated display strings whose meaning must remain safe in every locale |

A string may carry more than one classification, e.g. both
`localizable_display` and `guardrail_sensitive_display`.

---

## Weekly Review Renderer Strings

Source: `atlas/weekly_review/render.py`

### Document title and disclaimer

| String | Category | Localization candidate | Guardrail-sensitive | Notes |
|--------|----------|----------------------|--------------------|----|
| `Atlas Weekly Investment Review` | `localizable_display` | Yes | No | Module-level `_TITLE` constant |
| `Atlas Weekly Investment Review — deterministic, local-only, no recommendations.` | `localizable_display` | Yes | Yes | Part of `_DISCLAIMER`; "no recommendations" semantics must be preserved per locale |
| `Atlas supports better judgment. It does not replace it.` | `localizable_display` | Yes | Yes | Repeated in Section 10; core guardrail statement |

### Input Status section

Source: `_render_input_status()`

| String / Template | Category | Localization candidate | Guardrail-sensitive |
|------------------|----------|----------------------|-------------------|
| `## Input Status` | `localizable_display` | Yes | No |
| `Portfolio: N holding(s) loaded.` | `localizable_display` | Yes | No |
| `Watchlist: N item(s) loaded from 'NAME'.` | `localizable_display` | Yes | No |
| `Investor profile: Available` / `Not provided — default will be used.` | `localizable_display` | Yes | No |
| `Decision journal: N entry/entries loaded.` / `Not provided.` | `localizable_display` | Yes | No |
| `Company facts: Available` / `Not provided — evidence gaps noted.` | `localizable_display` | Yes | No |
| `Financials: Available` / `Not provided — evidence gaps noted.` | `localizable_display` | Yes | No |
| `Research notes: N ticker(s) with local notes.` / `Not provided.` | `localizable_display` | Yes | No |
| `Review date: DATE` | `localizable_display` | Yes | No |
| `Warnings: N` | `localizable_display` | Yes | No |

### Input Warnings section

Source: `_render_warnings()`

| String / Template | Category | Localization candidate | Guardrail-sensitive |
|------------------|----------|----------------------|-------------------|
| `## Input Warnings` | `localizable_display` | Yes | No |
| `[WARNING_CODE] MESSAGE` | Mixed: code is `canonical_internal`, message is `localizable_display` | Message: Yes | No |

### Section 1 — Review Scope

Source: `_section1_scope()`

| String / Template | Category | Localization candidate | Guardrail-sensitive |
|------------------|----------|----------------------|-------------------|
| `## 1. Review Scope` | `localizable_display` | Yes | No |
| `Review date: DATE` | `localizable_display` | Yes | No |
| `Review date: Not specified` | `localizable_display` | Yes | No |
| `Input mode: Local files only. No external data, no live pricing.` | `localizable_display` | Yes | Yes | Describes safety boundary |
| `Portfolio: N holding(s) across N account(s)` | `localizable_display` | Yes | No |
| `Watchlist: N item(s) in 'NAME'` | `localizable_display` | Yes | No |
| `Optional inputs loaded: …` | `localizable_display` | Yes | No |
| `Optional inputs: none provided — review uses portfolio and watchlist only` | `localizable_display` | Yes | No |
| `Scope notes: PREVIEW` | Mixed: label is `localizable_display`, preview is `user_content_passthrough` | Label: Yes | No |
| `Warnings: N input warning(s) noted — see Input Warnings section` | `localizable_display` | Yes | No |

### Section 2 — Portfolio Context

Source: `_section2_portfolio()`

| String / Template | Category | Localization candidate | Guardrail-sensitive |
|------------------|----------|----------------------|-------------------|
| `## 2. Portfolio Context` | `localizable_display` | Yes | No |
| `Account: NAME — N holding(s)` | `localizable_display` | Yes | No |
| `Holdings by weight (user-supplied values, highest first):` | `localizable_display` | Yes | No |
| `TICKER — NAME, SECTOR: WEIGHT% [ROLE]` | Mixed: template is `localizable_display`, values are `user_content_passthrough` | Template: Yes | No |
| `Sector exposure:` | `localizable_display` | Yes | No |
| `SECTOR: WEIGHT%` | Mixed: template is `localizable_display`, values are `user_content_passthrough` | Template: Yes | No |
| `Concentration note: … Single-position weight exceeds 25% threshold.` | `localizable_display` | Yes | Yes | Structural observation |
| `Combined concentration: … Top-2 combined exposure may warrant review.` | `localizable_display` | Yes | Yes | Structural observation |
| `Cash position: WEIGHT% of portfolio in cash or cash-equivalent holdings.` | `localizable_display` | Yes | No |
| `Unclassified sector: TICKERS — sector not specified in input.` | `localizable_display` | Yes | No |
| `Note: All values are user-supplied. No live pricing or external data used.` | `localizable_display` | Yes | Yes | Boundary statement |

### Section 3 — Watchlist Review

Source: `_section3_watchlist()`

| String / Template | Category | Localization candidate | Guardrail-sensitive |
|------------------|----------|----------------------|-------------------|
| `## 3. Watchlist Review` | `localizable_display` | Yes | No |
| `TICKER — NAME: STATUS_VALUE` | Mixed: template `localizable_display`, status value `canonical_internal` | Template: Yes | No |
| `[TICKER] Reason: TEXT` | Mixed: label `localizable_display`, text `user_content_passthrough` | Label: Yes | No |
| `[TICKER] Evidence Gap: TEXT` | Mixed: label `localizable_display` + `guardrail_sensitive_display`, text `user_content_passthrough` | Label: Yes | Yes |
| `[TICKER] Question: TEXT` | Mixed: label `localizable_display`, text `user_content_passthrough` | Label: Yes | No |
| `[TICKER] Observation: TEXT` | Mixed: label `localizable_display`, text `user_content_passthrough` | Label: Yes | No |
| `[TICKER] Notes: TEXT` | Mixed: label `localizable_display`, text `user_content_passthrough` | Label: Yes | No |
| `No watchlist items loaded.` | `localizable_display` | Yes | No |

### Section 4 — Company Reviews Needing Attention

Source: `_section4_attention()`

| String / Template | Category | Localization candidate | Guardrail-sensitive |
|------------------|----------|----------------------|-------------------|
| `## 4. Company Reviews Needing Attention` | `localizable_display` | Yes | No |
| `TICKER (NAME): Needs Review — held in portfolio … and under active watchlist review (Status: VALUE)` | Mixed: template `localizable_display`, status `canonical_internal` | Template: Yes | No |
| `TICKER (NAME): Needs More Evidence — N evidence gaps remain open. Status: VALUE.` | Mixed: template `localizable_display` + `guardrail_sensitive_display` | Template: Yes | Yes |
| `TICKER (NAME): Visible holding — WEIGHT% of loaded portfolio value in SECTOR sector.` | `localizable_display` | Yes | No |
| `TICKER: Missing Classification — sector not specified in input.` | `localizable_display` | Yes | No |
| `No items flagged for immediate attention from available local inputs.` | `localizable_display` | Yes | No |
| `Note: All observations are derived from user-supplied local inputs only. No external data, no engine analysis, no recommendations.` | `localizable_display` | Yes | Yes | "no recommendations" is guardrail-sensitive |

### Section 5 — Portfolio Fit and Suitability Notes

Source: `_section5_suitability()`

| String / Template | Category | Localization candidate | Guardrail-sensitive |
|------------------|----------|----------------------|-------------------|
| `## 5. Portfolio Fit and Suitability Notes` | `localizable_display` | Yes | No |
| `Investor profile: Provided.` / `Not provided. Suitability observations below are structural only and not personalized.` | `localizable_display` | Yes | Yes | "not personalized" is boundary statement |
| `Risk tolerance: VALUE` | Mixed: label `localizable_display`, value `user_content_passthrough` | Label: Yes | No |
| `Time horizon: VALUE` | Mixed: label `localizable_display`, value `user_content_passthrough` | Label: Yes | No |
| `Concentration observation: … Concentration should be reviewed in relation to stated constraints.` | `localizable_display` | Yes | No |
| `Cash position: WEIGHT% of portfolio. Review cash level in relation to investment goals.` | `localizable_display` | Yes | No |
| `Invested positions: N (excluding cash holdings).` | `localizable_display` | Yes | No |
| `Sector concentration: all invested holdings are in SECTOR. Diversification should be reviewed against stated constraints.` | `localizable_display` | Yes | No |
| `Stated constraints (from investor profile):` | `localizable_display` | Yes | No |
| `  Constraint: TEXT` | Mixed: label `localizable_display`, text `user_content_passthrough` | Label: Yes | No |
| `Full suitability evaluation is deferred until engine wiring. Portfolio fit notes are limited to loaded local structure.` | `localizable_display` | Yes | Yes | Boundary statement |
| `Note: Atlas does not judge investment merit or provide personalized guidance. Suitability assessment requires manual review.` | `localizable_display` | Yes | Yes | Core guardrail statement |

### Section 6 — Risk and Principle Guardrails

Source: `_section6_guardrails()`

| String / Template | Category | Localization candidate | Guardrail-sensitive |
|------------------|----------|----------------------|-------------------|
| `## 6. Risk and Principle Guardrails` | `localizable_display` | Yes | No |
| `Stated principles (from investor profile):` | `localizable_display` | Yes | No |
| `  Principle: TEXT` | Mixed: label `localizable_display`, text `user_content_passthrough` | Label: Yes | No |
| `Elevated risk scores (user-supplied, > 60):` | `localizable_display` | Yes | No |
| `  Risk to Monitor: TICKER — risk score N` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Cost basis not provided for: TICKERS. Performance baseline cannot be computed from available data.` | `localizable_display` | Yes | No |
| `Sector concentration: SECTOR represents WEIGHT% of invested holdings. Risk to Monitor: sector exposure may warrant review.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Evidence Gap: Company facts not loaded. Evidence quality cannot be assessed from available inputs.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Evidence Gap: Financial history not loaded. Financial trend analysis not available.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Risk and principle guardrail engine wiring is deferred to a later sprint.` | `localizable_display` | Yes | No |
| `Principle Guardrail: No action is warranted when evidence is incomplete.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `No guardrail flags raised from available local inputs.` | `localizable_display` | Yes | No |
| `Note: Guardrail checks are based on user-supplied data only. No live market data or external analysis used.` | `localizable_display` | Yes | Yes |

### Section 7 — Open Decisions

Source: `_section7_decisions()`

| String / Template | Category | Localization candidate | Guardrail-sensitive |
|------------------|----------|----------------------|-------------------|
| `## 7. Open Decisions` | `localizable_display` | Yes | No |
| `Decision journal: N entry/entries reviewed.` | `localizable_display` | Yes | No |
| `No decision journal provided. Open decisions not reviewed.` | `localizable_display` | Yes | No |
| `TITLE (DATE): STATUS` | Mixed: template `localizable_display`, title/status `user_content_passthrough` | Template: Yes | No |
| `[Aging Note] ASSET: Review date is older than 90 days (N days). Thesis assumptions may need to be rechecked.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes | Aging note |
| `[Date Missing] No decision date recorded; aging cannot be assessed.` | `localizable_display` | Yes | No |
| `[Follow-up] TEXT` | Mixed: label `localizable_display`, text `user_content_passthrough` | Label: Yes | No |
| `[View] TEXT` | Mixed: label `localizable_display`, text `user_content_passthrough` | Label: Yes | No |

### Section 8 — Missing Evidence

Source: `_section8_evidence()`

| String / Template | Category | Localization candidate | Guardrail-sensitive |
|------------------|----------|----------------------|-------------------|
| `## 8. Missing Evidence` | `localizable_display` | Yes | No |
| `Evidence Gap [TICKER]: TEXT` | Mixed: label `localizable_display` + `guardrail_sensitive_display`, text `user_content_passthrough` | Label: Yes | Yes |
| `Evidence Gap [TICKER]: no local company facts file or financial history file.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Evidence Gap [TICKER]: local company facts file is missing.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Evidence Gap [TICKER]: local financial history file is missing.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Evidence Gap [TICKER] (research notes): TEXT` | Mixed: label `localizable_display` + `guardrail_sensitive_display`, text `user_content_passthrough` | Label: Yes | Yes |
| `Missing Optional Input: Investor profile not provided.` | `localizable_display` | Yes | No |
| `Missing Optional Input: Decision journal not provided.` | `localizable_display` | Yes | No |
| `Missing Optional Input: Company facts directory not provided.` | `localizable_display` | Yes | No |
| `Missing Optional Input: Financial history directory not provided.` | `localizable_display` | Yes | No |
| `Missing Classification: TICKER — sector not specified.` | `localizable_display` | Yes | No |
| `No evidence gaps identified from available local inputs.` | `localizable_display` | Yes | No |

### Section 9 — Follow-Up Questions

Source: `_section9_questions()`

| String / Template | Category | Localization candidate | Guardrail-sensitive |
|------------------|----------|----------------------|-------------------|
| `## 9. Follow-Up Questions` | `localizable_display` | Yes | No |
| `[TICKER] Open questions:` | `localizable_display` | Yes | No |
| `  - TEXT` | `user_content_passthrough` | No — user content | No |
| `[TICKER] Research notes — open questions:` | `localizable_display` | Yes | No |
| `[TICKER] Risk to Monitor (research notes): TEXT` | Mixed: label `localizable_display` + `guardrail_sensitive_display`, text `user_content_passthrough` | Label: Yes | Yes |
| `Tickers without local company facts (N): TICKERS` | `localizable_display` | Yes | No |
| `Tickers without local financial history (N): TICKERS` | `localizable_display` | Yes | No |
| `What company facts are needed before changing the status of any watchlist item?` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Which financial trends should be reviewed before any watchlist decision changes?` | `localizable_display` | Yes | No |
| `What evidence would confirm or weaken the current assumptions for each open watchlist item?` | `localizable_display` | Yes | No |
| `No follow-up questions identified. Add open_questions to watchlist items to surface them here.` | `localizable_display` | Yes | No |

### Section 10 — Non-Actions / Reasons to Wait

Source: `_section10_nonactions()`

| String / Template | Category | Localization candidate | Guardrail-sensitive |
|------------------|----------|----------------------|-------------------|
| `## 10. Non-Actions / Reasons to Wait` | `localizable_display` | Yes | No |
| `Decision Deferred: TICKER — NAME. Status: VALUE.` | Mixed: template `localizable_display` + `guardrail_sensitive_display`, status `canonical_internal` | Template: Yes | Yes |
| `Reason to Wait: N evidence gap(s) identified across watchlist items. Gathering evidence is the appropriate next step.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Reason to Wait: Investor profile not provided. Structural suitability assessment is deferred.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Reason to Wait: Decision journal not provided. Open decisions and prior context are not available for this review.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Reason to Wait: Local company facts missing for N ticker(s) (TICKERS): thesis context is incomplete for these positions.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Reason to Wait: Local financial history missing for N ticker(s) (TICKERS): financial context is incomplete for these positions.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Reason to Wait: Company facts not loaded. Decision-relevant evidence is incomplete.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Reason to Wait: Financial history not loaded. Financial trend analysis is not available.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Reason to Wait: ASSET decision journal notes are older than 90 days (N days). Assumptions should be refreshed before changing decision status.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Reason to Wait [TICKER] (research notes): TEXT` | Mixed: label `localizable_display` + `guardrail_sensitive_display`, text `user_content_passthrough` | Label: Yes | Yes |
| `Reason to Wait: TICKER research notes contain N unresolved evidence gap(s). Gathering evidence is the appropriate next step.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Reason to Wait: Stated principles support a measured approach to evidence and decision discipline:` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `  — "PRINCIPLE"` | `user_content_passthrough` | No — user content | No |
| `No Action Warranted: Stated constraints apply to current portfolio and watchlist decisions:` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `  — "CONSTRAINT"` | `user_content_passthrough` | No — user content | No |
| `No Action Warranted: This review is informational only. All observations are based on user-supplied local inputs.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Reminder: No action is a valid and often appropriate outcome of a weekly review.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Atlas supports better judgment. It does not replace it.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |

---

## Snapshot CLI Renderer Strings

Source: `atlas/snapshot_input/render.py`

### snapshot validate

| String | Category | Localization candidate | Guardrail-sensitive |
|--------|----------|----------------------|-------------------|
| `Snapshot Draft Validation` | `localizable_display` | Yes | No |
| `Status: valid` | Mixed: label `localizable_display`, value is semantically `canonical_internal` | Yes | No |
| `Status: invalid` | Mixed | Yes | No |
| `Snapshot Type: VALUE` | Mixed: label `localizable_display`, VALUE is `canonical_internal` | Label: Yes | No |
| `Confidence: VALUE` | Mixed: label `localizable_display`, VALUE is `canonical_internal` | Label: Yes | No |
| `Confirmation Status: VALUE` | Mixed: label `localizable_display`, VALUE is `canonical_internal` | Label: Yes | No |
| `Target Local File: PATH` | Mixed: label `localizable_display`, PATH is `command_or_file_convention` | Label: Yes | No |
| `Related Tickers: TICKERS` | Mixed: label `localizable_display`, tickers are `user_content_passthrough` | Label: Yes | No |
| `Uncertainties:` / `Uncertainties: none` | `localizable_display` | Yes | No |
| `  - TEXT` | `user_content_passthrough` | No | No |
| `Missing Required Fields:` / `Missing Required Fields: none` | `localizable_display` | Yes | No |
| `Source Reference: TEXT` | Mixed: label `localizable_display`, text `user_content_passthrough` | Label: Yes | No |
| `Notes: TEXT` | Mixed: label `localizable_display`, text `user_content_passthrough` | Label: Yes | No |
| `Safety Boundary:` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `  - Draft validation does not write to Atlas local input files.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Error: MESSAGE` | Mixed: label `localizable_display`, message may be `localizable_display` | Yes | No |

### snapshot review

| String | Category | Localization candidate | Guardrail-sensitive |
|--------|----------|----------------------|-------------------|
| `Snapshot Draft Review` | `localizable_display` | Yes | No |
| `Status: reviewable` | Mixed | Yes | No |
| `Exportable: yes` / `Exportable: no` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `  Reason: only confirmed drafts are exportable.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Source:` | `localizable_display` | Yes | No |
| `  - Source Description: TEXT` | Mixed: label `localizable_display`, text `user_content_passthrough` | Label: Yes | No |
| `  - Raw Source Reference: TEXT` | Mixed: label `localizable_display`, text `user_content_passthrough` | Label: Yes | No |
| `  - Notes: TEXT` | Mixed: label `localizable_display`, text `user_content_passthrough` | Label: Yes | No |
| `Review Checklist:` | `localizable_display` | Yes | No |
| `  - Draft ID: present` / `missing` | `localizable_display` | Yes | No |
| `  - Extracted Fields: present` / `empty` | `localizable_display` | Yes | No |
| `  - Safety Boundary: visible` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Missing Required Fields (warnings — review before confirming):` | `localizable_display` | Yes | No |
| `Extracted Fields:` | `localizable_display` | Yes | No |
| `  - KEY: VALUE` | Mixed: key is `canonical_internal`, value is `user_content_passthrough` | No | No |
| `  (empty)` | `localizable_display` | Yes | No |
| `Blocking Issues:` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `  None` | `localizable_display` | Yes | No |
| `  - TEXT` | `localizable_display` (system-generated issue text) | Yes | No |
| `Research Notes Review:` | `localizable_display` | Yes | No |
| `  - Ticker: VALUE` / `missing` | Mixed: label `localizable_display`, ticker `user_content_passthrough` | Label: Yes | No |
| `  - Title: present` / `missing` | `localizable_display` | Yes | No |
| `  - Thesis Notes: present` / `missing` | `localizable_display` | Yes | No |
| `  - Evidence Gaps: present` / `missing` | `localizable_display` | Yes | No |
| `  - Open Questions: present` / `missing` | `localizable_display` | Yes | No |
| `  - Risks to Monitor: present` / `missing` | `localizable_display` | Yes | No |
| `  - Reasons to Wait: present` / `missing` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Safety Boundary:` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `  - Review is read-only.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `  - Review does not confirm the draft.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `  - Review does not write Atlas local input files.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |

### snapshot confirm

| String | Category | Localization candidate | Guardrail-sensitive |
|--------|----------|----------------------|-------------------|
| `Snapshot Draft Confirmation` | `localizable_display` | Yes | No |
| `Status: confirmed` | Mixed: label `localizable_display`, value `canonical_internal` | Label: Yes | No |
| `Status: blocked` | Mixed | Yes | No |
| `Status: invalid` | Mixed | Yes | No |
| `Note: input draft was already confirmed; a confirmed copy was written.` | `localizable_display` | Yes | No |
| `Input Draft: PATH` | Mixed: label `localizable_display`, path `user_content_passthrough` | Label: Yes | No |
| `Output Draft: PATH` | Mixed: label `localizable_display`, path `user_content_passthrough` | Label: Yes | No |
| `Snapshot Type: VALUE` | Mixed: label `localizable_display`, VALUE `canonical_internal` | Label: Yes | No |
| `Confirmation Status: confirmed` | Mixed: label `localizable_display`, value `canonical_internal` | Label: Yes | No |
| `Safety Boundary:` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `  - Original draft was not modified.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `  - No Atlas local input files were changed.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `  - Export commands must still be run separately.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Reason: TEXT` | `localizable_display` | Yes | No |
| `Error: MESSAGE` | `localizable_display` | Yes | No |

### snapshot reject

| String | Category | Localization candidate | Guardrail-sensitive |
|--------|----------|----------------------|-------------------|
| `Snapshot Draft Rejection` | `localizable_display` | Yes | No |
| `Status: rejected` | Mixed: label `localizable_display`, value `canonical_internal` | Label: Yes | No |
| `Note: input draft was already rejected; a rejected copy was written.` | `localizable_display` | Yes | No |
| `Note: input draft was confirmed; a rejected copy was written for this workflow branch.` | `localizable_display` | Yes | No |
| `Confirmation Status: rejected` | Mixed: label `localizable_display`, value `canonical_internal` | Label: Yes | No |
| `Safety Boundary:` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `  - Rejected drafts are not exportable.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |

### snapshot export-research-notes

| String | Category | Localization candidate | Guardrail-sensitive |
|--------|----------|----------------------|-------------------|
| `Research Notes Export` | `localizable_display` | Yes | No |
| `Status: written` | `localizable_display` | Yes | No |
| `Ticker: VALUE` | Mixed: label `localizable_display`, ticker `user_content_passthrough` | Label: Yes | No |
| `Output File: PATH` | Mixed: label `localizable_display`, path `command_or_file_convention` | Label: Yes | No |
| `Safety Boundary:` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `  - Only local research notes were written.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `  - No portfolio, watchlist, journal, or company facts files were changed.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Status: blocked` | `localizable_display` | Yes | No |
| `Reason: TEXT` | `localizable_display` | Yes | No |

### snapshot export-company-facts

| String | Category | Localization candidate | Guardrail-sensitive |
|--------|----------|----------------------|-------------------|
| `Company Facts Export` | `localizable_display` | Yes | No |
| `Status: written` | `localizable_display` | Yes | No |
| `Ticker: VALUE` | Mixed: label `localizable_display`, ticker `user_content_passthrough` | Label: Yes | No |
| `Output File: PATH` | Mixed: label `localizable_display`, path `command_or_file_convention` | Label: Yes | No |
| `Safety Boundary:` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `  - Only local company facts were written.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `  - No portfolio, watchlist, journal, or research notes files were changed.` | `localizable_display` + `guardrail_sensitive_display` | Yes | Yes |
| `Status: blocked` | `localizable_display` | Yes | No |
| `Reason: TEXT` | `localizable_display` | Yes | No |

---

## Canonical Internal Values Not To Localize

These values appear in display output but must not be translated as stored values.

### snapshot_type enum values

```
portfolio_snapshot
watchlist_snapshot
open_orders_snapshot
news_snapshot
external_analysis_snapshot
research_notes_snapshot
company_facts_snapshot
unknown_snapshot
```

### confirmation_status enum values

```
draft
needs_user_review
confirmed
rejected
superseded
```

### confidence enum values

```
low
medium
high
unknown
```

### watchlist status values

```
watchlist
needs_more_evidence
research
decision_deferred
not_suitable
```

### CLI command names

```
weekly-review
snapshot validate
snapshot review
snapshot confirm
snapshot reject
snapshot export-research-notes
snapshot export-company-facts
```

### CLI option names

```
--portfolio  --watchlist  --profile  --journal
--company-facts  --financials  --research-notes
--as-of  --scope-notes  --output-draft  --output-dir  --overwrite
--language  (reserved, not yet implemented)
```

### Schema field names

```
snapshot_type  confirmation_status  confidence
extracted_fields  uncertainties  missing_required_fields
target_local_file  draft_id  source_description
raw_source_reference  related_tickers  created_at  notes
```

### File and directory conventions

```
portfolio.json
watchlist.json
investor_profile.json
decision_journal.json
research_notes/<TICKER>/notes.md
company_facts/<TICKER>.json
financials/<TICKER>.csv
```

These values may appear in localized output (e.g. displayed to the user in a
sentence) but must remain unchanged in stored files and internal logic.

---

## User-Provided Content Passthrough

These are areas where user-supplied content passes through Atlas rendering
unchanged. They are not localization candidates — they are the user's own text.

| Context | Source |
|---------|--------|
| Watchlist item `reason` field | Watchlist JSON |
| Watchlist item `evidence_needed` items | Watchlist JSON |
| Watchlist item `open_questions` items | Watchlist JSON |
| Watchlist item `manual_observations` items | Watchlist JSON |
| Watchlist item `notes` field | Watchlist JSON |
| Profile `principles` items | Investor profile JSON |
| Profile `constraints` items | Investor profile JSON |
| Profile `risk_tolerance` value | Investor profile JSON |
| Profile `time_horizon` value | Investor profile JSON |
| Journal entry `atlas_view` / `view` | Decision journal JSON |
| Journal entry `follow_up_triggers` items | Decision journal JSON |
| Journal entry `decision_title` / `asset_or_idea` | Decision journal JSON |
| Scope notes content | Scope notes Markdown file |
| Research note bullet text | Notes Markdown files |
| Snapshot draft `source_description` | Draft JSON |
| Snapshot draft `notes` | Draft JSON |
| Snapshot draft `extracted_fields` values | Draft JSON |
| Company facts draft field values | Draft JSON |

Rule: only Atlas-generated surrounding labels and headings are localization
candidates. The content above is never a localization target.

---

## Safe-Language Guardrail Strings

The following string groups carry guardrail-sensitive semantics. When localized,
equivalent phrasing in the target locale must preserve the same meaning and must
pass per-locale guardrail tests before the locale is enabled.

Guardrail categories (from `AtlasLocalizationBoundary.md`): recommendation,
price-target, urgency, certainty, and execution-language. Each locale needs its
own prohibited-phrase list within each category before that locale is enabled.

| String group | Why guardrail-sensitive |
|-------------|------------------------|
| `Reason to Wait` labels | Must not be paraphrased as urgency or action pressure |
| `No Action Warranted` labels | Must preserve non-recommendation meaning |
| `Evidence Gap` labels | Must not be paraphrased as actionable signal |
| `Risk to Monitor` labels | Must not be paraphrased as sell signal |
| `Decision Deferred` labels | Must preserve deferred/non-committed meaning |
| `Safety Boundary:` blocks | Must preserve boundary semantics in full |
| `Exportable: yes/no` | Must accurately reflect exportability |
| `Blocking Issues:` | Must accurately reflect blocking |
| Disclaimer (`…no recommendations. Atlas supports better judgment…`) | Must not be softened or omitted |
| `No external data, no live pricing` | Boundary statement; must remain accurate |
| `no recommendations` / `no engine analysis` | Must be preserved per locale |
| `Atlas does not judge investment merit or provide personalized guidance` | Must be preserved per locale |

---

## Future Extraction Candidates

Priority order for extracting strings into locale-aware constants (not done in this sprint):

| Priority | Target | Rationale |
|----------|--------|-----------|
| 1 | Snapshot CLI command headings and status labels | Smallest scope; fewest strings; lowest risk |
| 2 | Snapshot CLI Safety Boundary text blocks | High guardrail value; bounded set |
| 3 | Weekly Review section titles (10 strings) | Well-bounded; structural; no logic change |
| 4 | Weekly Review section body labels (`Evidence Gap`, `Reason to Wait`, etc.) | Larger set; requires per-locale guardrail tests |
| 5 | Input Status section labels | Low risk; structural |
| 6 | Demo script stage headings | Lowest impact; informational only |

---

## Known Gaps

1. **No string catalog exists.** All display strings are inline in renderer
   functions. Phase 2 of the localization plan will extract them.

2. **No locale-aware renderer exists.** All rendering is English-only. Phase 2
   will add a rendering helper layer.

3. **No `--language` option exists.** Phase 3 will add it to selected commands.

4. **No Swedish or French guardrail lists exist.** Phase 4 must define and test
   these before non-English locales can be enabled.

5. **Many tests assert English output strings.** Tests that assert
   `"Status: confirmed"` or `"Reason to Wait"` will need updating if English
   is not the only test locale. Tests asserting canonical internal values (e.g.
   `result.confirmation_status == "confirmed"`) will not need updating.

6. **Safety Boundary text is the highest-risk string group to localize** because
   its semantics must be preserved exactly. Per-locale guardrail coverage must
   include boundary statement semantics, not just prohibited term lists.

7. **Section 10 contains the highest density of guardrail-sensitive strings.**
   Nearly every line in `_section10_nonactions()` is both `localizable_display`
   and `guardrail_sensitive_display`. This section requires the most thorough
   per-locale guardrail testing before any locale is enabled.

---

## Sprint 238 Recommendation

**Recommended target: Extract Snapshot CLI display strings into constants**

Snapshot CLI strings are smaller and more bounded than Weekly Review output.
Extracting them first (creating named constants in `render.py` for each
command heading, status label, and Safety Boundary block) creates a low-risk
localization foundation:

- No behavior change — constants replace inline literals
- Tests can assert against the same constants
- Provides the extraction pattern for the larger Weekly Review work
- Bounded scope: ~30 distinct string groups across 6 commands

**Alternative if Weekly Review localization is prioritized:**
Extract Weekly Review section titles into constants.

**Alternative if safety preparation is prioritized:**
Create Swedish guardrail list (Phase 4 prerequisite for Swedish output).

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [docs/AtlasLocalizationBoundary.md](AtlasLocalizationBoundary.md) | Localization boundary rules |
| [docs/InternalV1ReleaseCandidate.md](InternalV1ReleaseCandidate.md) | v1 release candidate status |
| [docs/DecisionLog.md](DecisionLog.md) | Sprint decisions |
